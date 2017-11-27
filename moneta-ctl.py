#!/usr/bin/env python3
from djangofloor.scripts import django, set_env

__author__ = 'Matthieu Gallet'

set_env(command_name='moneta-django')
django()
