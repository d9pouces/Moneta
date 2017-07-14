import logging
import os

import gnupg
import pkg_resources
from django.conf import settings
from django.core.signing import Signer, BadSignature
from django.utils.crypto import constant_time_compare
from django.utils.encoding import force_str, force_text
from django.utils.translation import ugettext as _

__author__ = 'flanker'
logger = logging.getLogger('django.requests')
GPG_CONF_FILENAME = pkg_resources.resource_filename('moneta', 'templates/gpg.conf')


try:
    if not os.path.isdir(settings.GNUPG_HOME):
        gnupg = None
        GPG = None
    else:
        GPG = gnupg.GPG(gnupghome=settings.GNUPG_HOME, gpgbinary=settings.GNUPG_PATH,
                        options=['--options', GPG_CONF_FILENAME])

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
            if self.sep not in signed_value:
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
    logger.error(_('unable to import gnugpg module.'))
