__author__ = 'flanker'

from django.conf.urls import include, url
from django.contrib import admin

admin.autodiscover()

urls = [
    url(r'^repo/', include('moneta.repository.urls')),
    url(r'^core/', include('moneta.urls', namespace='moneta')),
]
