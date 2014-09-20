#coding=utf-8
""" Django settings for Moneta project. """
from django.utils.six import u

__author__ = u('flanker')


import os
import sys
from django.utils.importlib import import_module
from moneta.core import defaults

SETTINGS_VARIABLE = 'MONETA_SETTINGS'
CONF_PATH = os.environ.get(SETTINGS_VARIABLE)

__conf_is_set = False
if not CONF_PATH:
    current_file_components = __file__.split(os.path.sep)
    if 'lib' in current_file_components:
        current_file_components = current_file_components[:current_file_components.index('lib')]
        current_file_components += ['etc', 'moneta', 'settings.py']
        CONF_PATH = os.path.sep.join(current_file_components)
if CONF_PATH and os.path.isfile(CONF_PATH):
    sys.path.append(os.path.dirname(CONF_PATH))
    conf_module = os.path.basename(CONF_PATH)[:-3]
    conf_settings = import_module(conf_module)
    __conf_is_set = True

    def option(name, default_value):
        if hasattr(conf_settings, name):
            return getattr(conf_settings, name)
        return default_value
else:
    # noinspection PyUnusedLocal
    def option(name, default_value):
        return default_value


__settings = globals()
for option_name, option_value in defaults.__dict__.items():
    if option_name == option_name.upper():
        __settings[option_name] = option(option_name, option_value)


CONF_IS_SET = __conf_is_set

if __name__ == '__main__':
    import doctest

    doctest.testmod()