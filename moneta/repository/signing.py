import logging
from functools import lru_cache

import gnupg
import pkg_resources
# noinspection PyPackageRequirements
from django.core.signing import Signer, BadSignature
# noinspection PyPackageRequirements
from django.utils.crypto import constant_time_compare

__author__ = 'flanker'
logger = logging.getLogger('django.requests')
GPG_CONF_FILENAME = pkg_resources.resource_filename('moneta', 'templates/gpg.conf')


@lru_cache()
def get_gpg():
    # noinspection PyPackageRequirements
    from django.conf import settings
    gpg = gnupg.GPG(homedir=settings.GNUPG_HOME, binary=settings.GNUPG_PATH,
                    secring='secring.gpg', keyring='pubring.gpg',
                    options=['--options', GPG_CONF_FILENAME])
    return gpg


class GPGSigner(Signer):
    def __init__(self, key=None, sep=':', salt=None):
        # noinspection PyPackageRequirements
        from django.conf import settings
        super().__init__(sep=sep, salt=salt)
        self.key = str(key or settings.GNUPG_KEYID)

    def signature(self, value):
        # noinspection PyPackageRequirements
        from django.conf import settings
        # noinspection PyUnresolvedReferences
        return str(get_gpg().sign(value, default_key=self.key, detach=True, digest_algo=settings.GNUPG_DIGEST_ALGO))

    def sign_file(self, fd, detach=True):
        # noinspection PyPackageRequirements
        from django.conf import settings
        # noinspection PyUnresolvedReferences
        return str(get_gpg().sign(fd, default_key=self.key, detach=detach, clearsign=not detach,
                                  digest_algo=settings.GNUPG_DIGEST_ALGO))

    def export_key(self):
        # noinspection PyUnresolvedReferences
        return get_gpg().export_keys(self.key)

    def sign(self, value):
        value = str(value)
        return str('%s%s%s') % (value, self.sep, self.signature(value))

    def unsign(self, signed_value):
        signed_value = str(signed_value)
        if self.sep not in signed_value:
            raise BadSignature('No "%s" found in value' % self.sep)
        value, sig = signed_value.rsplit(self.sep, 1)
        if constant_time_compare(sig, self.signature(value)):
            return str(value)
        raise BadSignature('Signature "%s" does not match' % sig)

    # noinspection PyMethodMayBeStatic
    def verify(self, value):
        # noinspection PyUnresolvedReferences
        return get_gpg().verify(value)

    # noinspection PyMethodMayBeStatic
    def verify_file(self, fd, path_to_data_file=None):
        # noinspection PyUnresolvedReferences
        return get_gpg().verify_file(fd, path_to_data_file)
