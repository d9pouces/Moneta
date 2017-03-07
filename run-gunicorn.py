#!/usr/bin/env python
# -*- coding: utf-8 -*-
from djangofloor.scripts import gunicorn
import os
os.environ['DJANGOFLOOR_PROJECT_NAME'] = 'moneta'
gunicorn()
