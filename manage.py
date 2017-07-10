#!/usr/bin/env python3
from djangofloor.scripts import manage
import os
os.environ['DJANGOFLOOR_PROJECT_NAME'] = 'moneta'
manage()
