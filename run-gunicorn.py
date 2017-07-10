#!/usr/bin/env python3
from djangofloor.scripts import gunicorn
import os
os.environ['DJANGOFLOOR_PROJECT_NAME'] = 'moneta'
gunicorn()
