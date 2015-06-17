# -*- coding: utf-8 -*-
__author__ = 'flanker'
from djangofloor.iniconf import OptionParser, bool_setting

def x_accel_converter(value):
    if bool_setting(value):
        return [('{MEDIA_ROOT}/', '{MEDIA_URL}'), ]
    return []


INI_MAPPING = [
    OptionParser('SERVER_NAME', 'global.server_name'),
    OptionParser('PROTOCOL', 'global.protocol'),
    OptionParser('BIND_ADDRESS', 'global.bind_address'),
    OptionParser('LOCAL_PATH', 'global.data_path'),
    OptionParser('ADMIN_EMAIL', 'global.admin_email'),
    OptionParser('TIME_ZONE', 'global.time_zone'),
    OptionParser('LANGUAGE_CODE', 'global.language_code'),
    OptionParser('USE_X_SEND_FILE', 'global.x_send_file', bool_setting),
    OptionParser('X_ACCEL_REDIRECT', 'global.x_accel_converter', x_accel_converter),
    OptionParser('FLOOR_AUTHENTICATION_HEADER', 'global.remote_user_header'),
    OptionParser('EXTRA_INSTALLED_APP', 'global.extra_app'),


    OptionParser('DATABASE_ENGINE', 'database.engine'),
    OptionParser('DATABASE_NAME', 'database.name'),
    OptionParser('DATABASE_USER', 'database.user'),
    OptionParser('DATABASE_PASSWORD', 'database.password'),
    OptionParser('DATABASE_HOST', 'database.host'),
    OptionParser('DATABASE_PORT', 'database.port'),

]
