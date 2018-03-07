import logging
import platform
import re
import shlex
import subprocess
from functools import lru_cache

import gnupg
import os
import pkg_resources
# noinspection PyPackageRequirements
from django.core.signing import Signer, BadSignature
# noinspection PyPackageRequirements
from django.utils.crypto import constant_time_compare

__author__ = 'flanker'
logger = logging.getLogger('django.requests')
GPG_CONF_FILENAME = pkg_resources.resource_filename('moneta', 'templates/gpg.conf')


class BatchGPG(gnupg.GPG):
    def __init__(self):
        # noinspection PyPackageRequirements
        from django.conf import settings
        self.patch_gpg_2_1 = False
        super().__init__(homedir=settings.GNUPG_HOME, binary=settings.GNUPG_PATH, secring='secring.gpg',
                         keyring='pubring.gpg', use_agent=False, options=['--options', GPG_CONF_FILENAME])
        matcher = re.match(r'(\d)\.(\d+)\.(\d+)', self.binary_version)
        if matcher:
            version = tuple(int(x) for x in matcher.groups())
            self.patch_gpg_2_1 = version >= (2, 1, 0)

    def _open_subprocess(self, args=None, passphrase=False):
        if not self.patch_gpg_2_1:
            return super()._open_subprocess(args=args, passphrase=passphrase)
        cmd = shlex.split(' '.join(self._make_args(args, passphrase)))
        if platform.system() == "Windows":
            # TODO figure out what the hell is going on there.
            expand_shell = True
        else:
            expand_shell = False

        environment = {
            'LANGUAGE': os.environ.get('LANGUAGE') or 'en',
            'DISPLAY': os.environ.get('DISPLAY') or '',
            'GPG_AGENT_INFO': os.environ.get('GPG_AGENT_INFO') or '',
            'GPG_TTY': os.environ.get('GPG_TTY') or '',
            'GPG_PINENTRY_PATH': os.environ.get('GPG_PINENTRY_PATH') or '',
        }
        return subprocess.Popen(cmd + ['--pinentry-mode', 'loopback'], shell=expand_shell, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                env=environment)


@lru_cache()
def get_gpg():
    return BatchGPG()


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
        return str(get_gpg().sign(value, default_key=self.key, detach=True, digest_algo=settings.GNUPG_DIGEST_ALGO,
                                  passphrase=settings.GNUPG_PASSPHRASE))

    def sign_file(self, fd, detach=True):
        # noinspection PyPackageRequirements
        from django.conf import settings
        # noinspection PyUnresolvedReferences
        return str(get_gpg().sign(fd, default_key=self.key, detach=detach, clearsign=not detach,
                                  digest_algo=settings.GNUPG_DIGEST_ALGO,
                                  passphrase=settings.GNUPG_PASSPHRASE))

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
