#coding=utf-8
"""Define mappings from the URL requested by a user to a proper Python view."""
from django.utils.six import u

__author__ = u('flanker')

from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin
from moneta.core.sitemap import CoreSiteMap

admin.autodiscover()

urlpatterns = patterns('', url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
                       (r'^grappelli/', include('grappelli.urls')),
url(r'^admin/', include(admin.site.urls)),
                   (r'^jsi18n/$', 'django.views.i18n.javascript_catalog',
                    {'packages': ('moneta', 'django.contrib.admin', ), }),
                   (r'^' + settings.MEDIA_URL[1:] + '(?P<path>.*)$', 'django.views.static.serve',
                    {'document_root': settings.MEDIA_ROOT}),
                   (r'^' + settings.STATIC_URL[1:] + '(?P<path>.*)$', 'django.views.static.serve',
                    {'document_root': settings.STATIC_ROOT}),
                   (r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': {'core': CoreSiteMap}}),
                   (r'^robots\.txt$', 'moneta.core.views.robots'),
                   # URL from different kind of repositories
                   (r'^repo/', include('moneta.repository.urls')),
                   # general operations on repositories
                   (r'^core/', include('moneta.core.urls')),
                   # index
                   url(r'^$', 'moneta.core.views.default'),
                       )