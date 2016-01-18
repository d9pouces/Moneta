# -*- coding: utf-8 -*-
from djangofloor.utils import DirectoryPath

__author__ = 'flanker'

FLOOR_URL_CONF = 'moneta.root_urls.urls'
FLOOR_INSTALLED_APPS = ['moneta', 'moneta.repositories', 'moneta.repository', ]
FLOOR_INDEX = 'moneta.views.index'
FLOOR_PROJECT_NAME = 'Moneta'
BIND_ADDRESS = '127.0.0.1:8131'

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
    'moneta.repositories.yum.Yum',
    'moneta.repositories.ruby.RubyGem',
    'moneta.repositories.jetbrains.Jetbrains',
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
]
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Already defined Django-related contexts here
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
                'django.template.context_processors.request',
            ],
        },
    },
]

STORAGES = {
    'archive': {
        'ENGINE': 'moneta.repository.storages.FlatStorage',
        'ROOT': DirectoryPath('{MEDIA_ROOT}/archives'),
        'PATH_LEN': 1,
    },
    'default': {
        'ENGINE': 'moneta.repository.storages.FlatStorage',
        'ROOT': DirectoryPath('{MEDIA_ROOT}/uncompressed'),
        'PATH_LEN': 1,
    },
    'cache': {
        'ENGINE': 'moneta.repository.storages.FlatStorage',
        'ROOT': DirectoryPath('{MEDIA_ROOT}/cache'),
        'PATH_LEN': 1,
    }
}

STORAGE_ARCHIVE = 'archive'
STORAGE_UNCOMPRESSED = 'uncompressed'
STORAGE_CACHE = 'cache'
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}

FLOOR_FAKE_AUTHENTICATION_USERNAME = None
DEBUG = False
# TO BE CONFIGURED
GNUPG_HOME = DirectoryPath('{LOCAL_PATH}/gpg')
GNUPG_HOME_HELP = 'Path of the GnuPG secret data'
# TO BE CONFIGURED
TEMP_ROOT = DirectoryPath('{LOCAL_PATH}/tmp')
TEMP_ROOT_HELP = 'Path used for temporary archive storage'
# TO BE CONFIGURED
GNUPG_KEYID = '1DA759EA7F5EF06F'
GNUPG_KEYID_HELP = 'ID of the GnuPG key'
# TO BE CONFIGURED
GNUPG_PATH = 'gpg'
GNUPG_PATH_HELP = 'Path of the gpg binary'