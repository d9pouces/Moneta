# coding=utf-8
""" Django settings for Moneta project. """
from django.utils.six import u

__author__ = u('flanker')

import os
from os.path import join, dirname, abspath
CONF_IS_SET = False
# define a root path for misc. Django data (SQLite database, static files, ...)
LOCAL_PATH = abspath(join(dirname(dirname(dirname(__file__))), 'django_data'))

# TO BE CONFIGURED
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': join(LOCAL_PATH, 'database.sqlite3'),  # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': '',
        'PASSWORD': '',
        'HOST': '',  # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',  # Set to empty string for default.
    },
}

DATABASE_ROUTERS = ['moneta.core.routers.BaseRouter', ]

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts

SITE_ID = 1
USE_I18N = True
USE_L10N = True
USE_TZ = True
MEDIA_URL = '/media/'
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    abspath(join(dirname(__file__), 'static')),
)
STATICFILES_FINDERS = ['django.contrib.staticfiles.finders.AppDirectoriesFinder',
                       'django.contrib.staticfiles.finders.FileSystemFinder', ]
TEMPLATE_LOADERS = [
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
]

WSGI_APPLICATION = 'moneta.core.wsgi.application'
TEMPLATE_DIRS = (
    abspath(join(dirname(__file__), 'templates')),
)
GRAPPELLI_ADMIN_TITLE = 'Administration'
ROOT_URLCONF = 'moneta.core.root_urls'
INTERNAL_IPS = ('127.0.0.1', )
DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
]
DEBUG_TOOLBAR_PATCH_SETTINGS = False
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.admin',
    'bootstrap3',
    'moneta.core',
    'moneta.repository',
    'moneta.repositories',
    'grappelli',
]

BOOTSTRAP3 = {
    'jquery_url': STATIC_URL + 'js/jquery.min.js',
    'base_url': STATIC_URL + 'bootstrap3/',
    'css_url': None,
    'theme_url': None,
    'javascript_url': None,
    'horizontal_label_class': 'col-md-2',
    'horizontal_field_class': 'col-md-4',
}


ARCHIVE_FILTERS = [
    'moneta.repository.filters.informations',
    # 'moneta.repository.filters.deb_archive',
]
REPOSITORY_CLASSES = [
    'moneta.repositories.aptitude.Aptitude',
    'moneta.repositories.pypi.Pypi',
    'moneta.repositories.maven3.Maven3',

]
SECRET_KEY = 'kg0ohOjT3WxuYejDf4Q0VPzxldt4Q3FzmEaoMskYH5OyVxoq4X'
MIDDLEWARE_CLASSES = [
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'moneta.core.middleware.MonetaRemoteUserMiddleware',
    'moneta.core.middleware.FakeAuthenticationMiddleware',
    'moneta.core.middleware.BasicAuthMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'moneta.core.middleware.IEMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
]
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.request',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'moneta.core.context_processors.context_base',
)
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.RemoteUserBackend',
    'django.contrib.auth.backends.ModelBackend',
]
# TO BE CONFIGURED
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache', }, }

# TO BE CONFIGURED
DEBUG = True
# TO BE CONFIGURED
TEMPLATE_DEBUG = DEBUG

# TO BE CONFIGURED
ADMINS = (("flanker", "flanker@19pouces.net"), )
# TO BE CONFIGURED
MANAGERS = ADMINS

# TO BE CONFIGURED
MEDIA_ROOT = join(LOCAL_PATH, 'media')
# TO BE CONFIGURED
STATIC_ROOT = join(LOCAL_PATH, 'static')
UPLOAD_ROOT = 'uploads'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
# TO BE CONFIGURED
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'color_console': {
            'level': 'INFO',
            'filters': [],
            'class': 'moneta.core.utils.ColorizedHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'moneta.files': {
            'handlers': ['mail_admins'],
            'level': 'INFO',
            'propagate': True,

        }
    }
}

# TO BE CONFIGURED
STORAGES = {
    'archive': {
        'ENGINE': 'moneta.core.storages.FlatStorage',
        'ROOT': os.path.join(LOCAL_PATH, 'archives'),
        'PATH_LEN': 1,
    },
    'default': {
        'ENGINE': 'moneta.core.storages.FlatStorage',
        'ROOT': os.path.join(LOCAL_PATH, 'uncompressed'),
        'PATH_LEN': 1,
    },
    'cache': {
        'ENGINE': 'moneta.core.storages.FlatStorage',
        'ROOT': os.path.join(LOCAL_PATH, 'cache'),
        'PATH_LEN': 1,
    }
}

STORAGE_ARCHIVE = 'archive'
STORAGE_UNCOMPRESSED = 'uncompressed'
STORAGE_CACHE = 'cache'

# TO BE CONFIGURED
GNUPG_HOME = os.path.join(LOCAL_PATH, 'gpg')
# TO BE CONFIGURED
TEMP_ROOT = os.path.join(LOCAL_PATH, 'tmp')
# TO BE CONFIGURED
GNUPG_KEYID = '64BCA36C3C47B697'
# TO BE CONFIGURED
GNUPG_PATH = '/usr/local/Cellar/gnupg/1.4.18/bin/gpg'

# TO BE CONFIGURED
ALLOWED_HOSTS = []
# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
# TO BE CONFIGURED
TIME_ZONE = 'Europe/Paris'
# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
# TO BE CONFIGURED
LANGUAGE_CODE = 'fr-fr'
# TO BE CONFIGURED
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# TO BE CONFIGURED
USE_X_FORWARDED_HOST = True
# TO BE CONFIGURED
AUTHENTICATION_HEADER = 'REMOTE_USER'
# TO BE CONFIGURED
FAKE_AUTHENTICATION_USERNAME = 'flanker'
TEST_RUNNER = 'django.test.runner.DiscoverRunner'
# TO BE CONFIGURED  => use X-Sendfile header, header['X-Sendfile'] = the absolute_path of the file to send
USE_X_SEND_FILE = False
# TO BE CONFIGURED  => use X-Accel-Redirect header, = X_ACCEL_REDIRECT_ARCHIVE + relative path to send
X_ACCEL_REDIRECT_ARCHIVE = None
# TO BE CONFIGURED  => use X-Accel-Redirect header, = X_ACCEL_REDIRECT_UNCOMPRESSED + relative path to send
X_ACCEL_REDIRECT_UNCOMPRESSED = None
# TO BE CONFIGURED  => use X-Accel-Redirect header, = X_ACCEL_REDIRECT_CACHE + relative path to send
X_ACCEL_REDIRECT_CACHE = None
# TO BE CONFIGURED
EMAIL_HOST = 'localhost'
# TO BE CONFIGURED
EMAIL_HOST_PASSWORD = ''
# TO BE CONFIGURED
EMAIL_HOST_USER = ''
# TO BE CONFIGURED
EMAIL_PORT = 25
# TO BE CONFIGURED
EMAIL_SUBJECT_PREFIX = '[Moneta]'
# TO BE CONFIGURED
EMAIL_USE_TLS = False
# TO BE CONFIGURED
EMAIL_USE_SSL = False
# TO BE CONFIGURED
SERVER_EMAIL = 'root@localhost'