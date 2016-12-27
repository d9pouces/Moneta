# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, absolute_import

from djangofloor.log import generate_log_configuration

__author__ = 'Matthieu Gallet'


def moneta_log_configuration(log_directory=None, project_name=None, script_name=None, debug=False, log_remote_url=None):
    config = generate_log_configuration(log_directory=log_directory, project_name=project_name, script_name=script_name,
                                        debug=debug, log_remote_url=log_remote_url)
    config['loggers']['gnupg'] = {'handlers': [], 'level': 'ERROR', 'propagate': True}
    return config
