# coding=utf-8
""" Django settings for Moneta project. """
from django.utils.six import u

__author__ = u('flanker')

import os
from os.path import join, dirname, abspath
CONF_IS_SET = False
# define a root path for misc. Django data (SQLite database, static files, ...)
LOCAL_PATH = abspath(join(dirname(dirname(dirname(__file__))), 'django_data'))


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
    'grappelli',
    'django.contrib.admin',
    'pipeline',
    'bootstrap3',
    'moneta.core',
    'moneta.repository',
    'moneta.repositories',
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


# Pipeline configuration

PIPELINE_JS = {
    'base': {'source_filenames': ['js/jquery.min.js', 'bootstrap3/js/bootstrap.min.js', ],
             'output_filename': 'js/base.js', },
}
PIPELINE_CSS = {
    'base': {'source_filenames': ['bootstrap3/css/bootstrap.min.css', ],
             'output_filename': 'css/base.css', 'extra_context': {'media': 'all'}, }, }
PIPELINE_MIMETYPES = (
    ('text/coffeescript', '.coffee'),
    ('text/less', '.less'),
    ('text/javascript', '.js'),  # required for IE8
    ('text/x-sass', '.sass'),
    ('text/x-scss', '.scss')
)


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
    'pipeline.middleware.MinifyHTMLMiddleware',
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
PIPELINE_ENABLED = False
PIPELINE_CSS_COMPRESSOR = None
PIPELINE_JS_COMPRESSOR = None
PIPELINE_DISABLE_WRAPPER = True
STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache', }, }

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (("flanker", "flanker@19pouces.net"), )
MANAGERS = ADMINS

MEDIA_ROOT = join(LOCAL_PATH, 'media')
UPLOAD_ROOT = 'uploads'
STATIC_ROOT = join(LOCAL_PATH, 'static')

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
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

GNUPG_HOME = os.path.join(LOCAL_PATH, 'gpg')
TEMP_ROOT = os.path.join(LOCAL_PATH, 'tmp')
GNUPG_KEYID = '64BCA36C3C47B697'
GNUPG_PATH = '/usr/local/Cellar/gnupg/1.4.16/bin/gpg'

ALLOWED_HOSTS = []
# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Europe/Paris'
# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'fr-fr'
# FILE_UPLOAD_TEMP_DIR = '/tmp
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
AUTHENTICATION_HEADER = 'REMOTE_USER'
FAKE_AUTHENTICATION_USERNAME = None
TEST_RUNNER = 'django.test.runner.DiscoverRunner'
