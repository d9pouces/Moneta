# -*- coding: utf-8 -*-
from djangofloor.utils import DirectoryPath

__author__ = 'flanker'
from django.utils.translation import ugettext_lazy as _

FLOOR_URL_CONF = 'moneta.root_urls.urls'
EXTRA_INSTALLED_APP = 'bootstrap3'
FLOOR_INSTALLED_APPS = ['moneta', 'moneta.repositories', 'moneta.repository', '{EXTRA_INSTALLED_APP}']
FLOOR_INDEX = 'moneta.views.index'
FLOOR_PROJECT_NAME = _('Moneta')

UPLOAD_ROOT = 'uploads'
ARCHIVE_FILTERS = [
    'moneta.repository.filters.informations',
    # 'moneta.repository.filters.deb_archive',
]
REPOSITORY_CLASSES = [
    'moneta.repositories.aptitude.Aptitude',
    'moneta.repositories.pypi.Pypi',
    'moneta.repositories.maven3.Maven3',
    'moneta.repositories.flat_files.FlatFile',
]

TEMPLATE_CONTEXT_PROCESSORS = [
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.request',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'djangofloor.context_processors.context_base',
    'moneta.context_processors.context_base',
    'allauth.account.context_processors.account',
    'allauth.socialaccount.context_processors.socialaccount',
]

STORAGES = {
    'archive': {
        'ENGINE': 'moneta.repository.storages.FlatStorage',
        'ROOT': DirectoryPath('{LOCAL_PATH}/storage/archives'),
        'PATH_LEN': 1,
    },
    'default': {
        'ENGINE': 'moneta.repository.storages.FlatStorage',
        'ROOT': DirectoryPath('{LOCAL_PATH}/storage/uncompressed'),
        'PATH_LEN': 1,
    },
    'cache': {
        'ENGINE': 'moneta.repository.storages.FlatStorage',
        'ROOT': DirectoryPath('{LOCAL_PATH}/storage/cache'),
        'PATH_LEN': 1,
    }
}

STORAGE_ARCHIVE = 'archive'
STORAGE_UNCOMPRESSED = 'uncompressed'
STORAGE_CACHE = 'cache'
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}

FLOOR_FAKE_AUTHENTICATION_USERNAME = 'flanker'
DEBUG = True
# TO BE CONFIGURED
GNUPG_HOME = DirectoryPath('{LOCAL_PATH}/gpg')
# TO BE CONFIGURED
TEMP_ROOT = DirectoryPath('{LOCAL_PATH}/tmp')
# TO BE CONFIGURED
GNUPG_KEYID = '1DA759EA7F5EF06F'
# TO BE CONFIGURED
GNUPG_PATH = '/usr/local/Cellar/gnupg/1.4.18/bin/gpg'
