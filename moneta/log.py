# -*- coding: utf-8 -*-
from djangofloor.log import log_configuration

__author__ = 'Matthieu Gallet'


def moneta_log_configuration(settings_dict):
    config = log_configuration(settings_dict)
    config['loggers']['gnupg'] = {'handlers': [], 'level': 'ERROR', 'propagate': True}
    return config

# noinspection PyUnresolvedReferences
moneta_log_configuration.required_settings = log_configuration.required_settings
