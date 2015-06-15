# -*- coding: utf-8 -*-
__author__ = 'flanker'
# coding=utf-8

from django.conf.urls import include, url
from django.contrib import admin

admin.autodiscover()

urls = [
    (r'^repo/', include('moneta.repository.urls')),
    (r'^core/', include('moneta.urls')),

]
