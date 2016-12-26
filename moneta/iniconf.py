# -*- coding: utf-8 -*-
from djangofloor.conf.fields import bool_setting, CharConfigField, ConfigField
from djangofloor.conf.mapping import NOREDIS_MAPPING

__author__ = 'flanker'


def x_accel_converter(value):
    if bool_setting(value):
        return [('{MEDIA_ROOT}/', '/p/get/'),
                ('{MEDIA_ROOT}/', '/a/get/'), ]
    return []


INI_MAPPING = NOREDIS_MAPPING + [
    ConfigField('global.use_apache', 'USE_X_SEND_FILE', from_str=bool_setting,
                help_str='Apache only. Set it to "true" or "false"'),
    ConfigField('global.use_nginx', 'X_ACCEL_REDIRECT', from_str=x_accel_converter,
                help_str='Nginx only. Set it to "true" or "false"', to_str=lambda x: str(bool(x))),
    CharConfigField('gnupg.home', 'GNUPG_HOME', help_str='Path of the GnuPG secret data'),
    CharConfigField('gnupg.keyid', 'GNUPG_KEYID', help_str='ID of the GnuPG key'),
    CharConfigField('gnupg.path', 'GNUPG_PATH', help_str='Path of the gpg binary'),

]
