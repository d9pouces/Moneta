from django.conf import settings
from django.core.signing import Signer, base64_hmac, BadSignature
from django.utils.crypto import constant_time_compare
from django.utils.encoding import force_str, force_text
from django.utils.translation import ugettext as _
import gnupg
import logging

__author__ = 'flanker'


class RSASigner(Signer):

    def __init__(self, key=None, sep=':', salt=None):
        super().__init__(sep=sep, salt=salt)
        self.key = str(key or settings.RSA_SECRET_KEY)

    def signature(self, value):
        signature = base64_hmac(self.salt + 'signer', value, self.key)
        # Convert the signature from bytes to str only on Python 3
        return force_str(signature)

    def sign_file(self, fd):
        return self.signature(fd.read())


class DSASigner(RSASigner):

    def __init__(self, key=None, sep=':', salt=None):
        super().__init__(sep=sep, salt=salt)
        self.key = str(key or settings.DSA_SECRET_KEY)

    def signature(self, value):
        signature = base64_hmac(self.salt + 'signer', value, self.key)
        # Convert the signature from bytes to str only on Python 3
        return force_str(signature)

try:
    GPG = gnupg.GPG(gnupghome=settings.GNUPG_HOME, gpgbinary=settings.GNUPG_PATH)

    class GPGSigner(Signer):

        def __init__(self, key=None, sep=':', salt=None):
            super().__init__(sep=sep, salt=salt)
            self.key = str(key or settings.GNUPG_KEYID)

        def signature(self, value):
            return force_str(GPG.sign(value, keyid=self.key, detach=True))

        def sign_file(self, fd):
            # noinspection PyProtectedMember
            return force_str(GPG.sign_file(fd, keyid=self.key, detach=True))

        def export_key(self):
            return GPG.export_keys(self.key)

        def sign(self, value):
            value = force_str(value)
            return str('%s%s%s') % (value, self.sep, self.signature(value))

        def unsign(self, signed_value):
            signed_value = force_str(signed_value)
            if not self.sep in signed_value:
                raise BadSignature('No "%s" found in value' % self.sep)
            value, sig = signed_value.rsplit(self.sep, 1)
            if constant_time_compare(sig, self.signature(value)):
                return force_text(value)
            raise BadSignature('Signature "%s" does not match' % sig)

        # noinspection PyMethodMayBeStatic
        def verify(self, value):
            return GPG.verify(value)

        # noinspection PyMethodMayBeStatic
        def verify_file(self, fd, path_to_data_file=None):
            return GPG.verify_file(fd, path_to_data_file)

except ImportError:
    gnupg = None
    GPG = None
    logging.warning(_('unable to import gnugpg module.'))