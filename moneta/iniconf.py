# -*- coding: utf-8 -*-
__author__ = 'flanker'
from djangofloor.iniconf import OptionParser, bool_setting, INI_MAPPING as DEFAULTS


def x_accel_converter(value):
    if bool_setting(value):
        return [('{MEDIA_ROOT}/', '/p/get/'),
                ('{MEDIA_ROOT}/', '/a/get/'), ]
    return []


INI_MAPPING = DEFAULTS + [
    OptionParser('USE_X_SEND_FILE', 'global.x_send_file', bool_setting, doc_default_value=True),
    OptionParser('X_ACCEL_REDIRECT', 'global.x_accel_converter', x_accel_converter,
                 help_str='Nginx only. Set it to "true" or "false"', to_str=lambda x: 'True' if x else 'False'),
    OptionParser('GNUPG_HOME', 'gnupg.home'),
    OptionParser('GNUPG_KEYID', 'gnupg.keyid'),
    OptionParser('GNUPG_PATH', 'gnupg.path'),

]
