# coding=utf-8
"""
Define a main() function, allowing you to manage your Django project.
"""
from django.utils.six import u

__author__ = u('flanker')


import os
import sys
from django import get_version
from django.core.management import LaxOptionParser


def set_env():
    """Set the path of the configuration file.
    This configuration file must be a valid Python file, which can be put anywhere.
    """
    conf_path = os.path.abspath('moneta_configuration.py')
    if not os.path.isfile(conf_path):
        splitted_path = __file__.split(os.path.sep)
        if 'lib' in splitted_path:
            splitted_path = splitted_path[:splitted_path.index('lib')] + ['etc', 'moneta_configuration.py']
            conf_path = os.path.sep.join(splitted_path)
            if not os.path.isfile(conf_path):
                conf_path = ''

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "moneta.core.settings")
    parser = LaxOptionParser(usage="%prog subcommand [options] [args]", version=get_version(), option_list=[])
    parser.add_option('--conf_file', action='store', default=conf_path, help=u('configuration file'))
    options, args = parser.parse_args(sys.argv)
    os.environ.setdefault("MONETA_SETTINGS", options.conf_file)
    sys.argv = args
    return args


def main():
    """
    Main function, calling Django code for management commands.
    """
    args = set_env()
    from django.core.management import execute_from_command_line
    execute_from_command_line(args)


def gunicorn():
    from gunicorn.app.wsgiapp import run

    set_env()
    application = 'moneta.core.wsgi:application'
    if application not in sys.argv:
        sys.argv.append(application)
    run()
