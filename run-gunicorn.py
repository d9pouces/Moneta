#!/usr/bin/env python3
from djangofloor.scripts import gunicorn, set_env

__author__ = 'Matthieu Gallet'

set_env(command_name='moneta-gunicorn')
gunicorn()
