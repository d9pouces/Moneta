from djangofloor.conf.fields import bool_setting, CharConfigField
from djangofloor.conf.mapping import BASE_MAPPING, REDIS_MAPPING, AUTH_MAPPING, SENDFILE_MAPPING, ALLAUTH_MAPPING

__author__ = 'flanker'


def x_accel_converter(value):
    if bool_setting(value):
        return [('{MEDIA_ROOT}/', '/p/get/'),
                ('{MEDIA_ROOT}/', '/a/get/'), ]
    return []


INI_MAPPING = BASE_MAPPING + AUTH_MAPPING + ALLAUTH_MAPPING + REDIS_MAPPING + SENDFILE_MAPPING + [
    CharConfigField('gnupg.home', 'GNUPG_HOME', help_str='Path of the GnuPG secret data'),
    CharConfigField('gnupg.keyid', 'GNUPG_KEYID', help_str='ID of the GnuPG key'),
    CharConfigField('gnupg.path', 'GNUPG_PATH', help_str='Path of the gpg binary'),
    CharConfigField('gnupg.passphrase', 'GNUPG_PASSPHRASE', help_str='Passphrase of the GPG key'),

]
