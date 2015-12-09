# -*- coding: utf-8 -*-
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_SUBJECT_PREFIX = '[localhost] '
ACCOUNT_EMAIL_VERIFICATION = None
ADMINS = [['admin', 'admin@localhost']]
ADMIN_EMAIL = 'admin@localhost'
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
ARCHIVE_FILTERS = ['moneta.repository.filters.informations']
AUTHENTICATION_BACKENDS = ['djangofloor.backends.DefaultGroupRemoteUserBackend', 'django.contrib.auth.backends.ModelBackend',
                           'allauth.account.auth_backends.AuthenticationBackend']
BIND_ADDRESS = '127.0.0.1:9000'
BOOTSTRAP3 = {'horizontal_field_class': 'col-md-8', 'theme_url': None, 'jquery_url': '/static/js/jquery.min.js', 'horizontal_label_class': 'col-md-4', 'css_url': None, 'javascript_url': None,
              'base_url': '/static/bootstrap3/'}
BROKER_URL = 'redis://localhost:6379/13'
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}
CACHE_BACKEND = 'django.core.cache.backends.dummy.DummyCache'
CELERY_ACCEPT_CONTENT = ['json', 'yaml', 'msgpack']
CELERY_APP = 'djangofloor'
CELERY_CREATE_DIRS = True
CELERY_RESULT_EXCHANGE = 'moneta_results'
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/Paris'
CONN_MAX_AGE = 600
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SECURE = False
DAB_FIELD_RENDERER = 'django_admin_bootstrapped.renderers.BootstrapFieldRenderer'
DATABASES = {'default': {'TEST': {'CHARSET': None, 'COLLATION': None, 'NAME': None, 'MIRROR': None}, 'ENGINE': 'django.db.backends.sqlite3', 'OPTIONS': {}, 'HOST': '',
                         'NAME': 'django_data/data/database.sqlite3',
             'USER': '', 'ATOMIC_REQUESTS': False, 'PORT': '', 'TIME_ZONE': 'UTC', 'PASSWORD': '', 'CONN_MAX_AGE': 0, 'AUTOCOMMIT': True}}
DATABASE_ENGINE = 'django.db.backends.sqlite3'
DATABASE_HOST = ''
DATABASE_NAME = 'django_data/data/database.sqlite3'
DATABASE_PASSWORD = ''
DATABASE_PORT = ''
DATABASE_USER = ''
DATA_PATH = 'django_data/data'
DEBUG = True
DEBUG_TOOLBAR_CONFIG = {'JQUERY_URL': None}
DEBUG_TOOLBAR_PANELS = ['debug_toolbar.panels.versions.VersionsPanel', 'debug_toolbar.panels.timer.TimerPanel', 'debug_toolbar.panels.profiling.ProfilingPanel',
                        'debug_toolbar.panels.settings.SettingsPanel', 'debug_toolbar.panels.headers.HeadersPanel', 'debug_toolbar.panels.request.RequestPanel', 'debug_toolbar.panels.sql.SQLPanel',
                        'debug_toolbar.panels.staticfiles.StaticFilesPanel', 'debug_toolbar.panels.templates.TemplatesPanel', 'debug_toolbar.panels.cache.CachePanel',
                        'debug_toolbar.panels.signals.SignalsPanel', 'debug_toolbar.panels.redirects.RedirectsPanel']
DEBUG_TOOLBAR_PATCH_SETTINGS = False
DEFAULT_CHARSET = 'utf-8'
DEFAULT_CONTENT_TYPE = 'text/html'
DEFAULT_FROM_EMAIL = 'admin@localhost'
DF_WS_FACILITY = 'djangofloor'
DJANGOFLOOR_CONFIG_PATH = 'django_data/etc/moneta/settings.ini'
DJANGOFLOOR_MAPPING = 'moneta.iniconf:INI_MAPPING'
EMAIL_SUBJECT_PREFIX = '[localhost] '
EXTRA_INSTALLED_APP = 'bootstrap3'
FILE_CHARSET = 'utf-8'
FILE_UPLOAD_TEMP_DIR = None
FLOOR_AUTHENTICATION_HEADER = 'HTTP_REMOTE_USER'
FLOOR_DEFAULT_GROUP_NAME = 'Users'
FLOOR_FAKE_AUTHENTICATION_GROUPS = ['group1', 'group2']
FLOOR_FAKE_AUTHENTICATION_USERNAME = 'flanker'
FLOOR_INDEX = 'moneta.views.index'
FLOOR_INSTALLED_APPS = ['moneta', 'moneta.repositories', 'moneta.repository', 'bootstrap3']
FLOOR_PROJECT_NAME = 'Moneta'
FLOOR_URL_CONF = 'moneta.root_urls.urls'
FLOOR_USE_WS4REDIS = False
GNUPG_HOME = 'django_data/gpg'
GNUPG_KEYID = '1DA759EA7F5EF06F'
GNUPG_PATH = '/usr/local/Cellar/gnupg/1.4.18/bin/gpg'
INSTALLED_APPS = ['django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles', 'django.contrib.humanize',
                  'django.contrib.sites', 'django.contrib.sitemaps', 'django_admin_bootstrapped', 'django.contrib.admin', 'bootstrap3', 'djangofloor', 'allauth', 'allauth.account',
                  'allauth.socialaccount', 'pipeline', 'debug_toolbar', 'moneta', 'moneta.repositories', 'moneta.repository']
INTERNAL_IPS = ['127.0.0.1']
LANGUAGE_CODE = 'en-us'
LOCAL_PATH = 'django_data/var/moneta'
LOGGING = {'loggers': {'django.request': {'level': 'ERROR', 'handlers': ['mail_admins', 'stream'], 'propagate': True}},
           'filters': {'require_debug_false': {'()': 'django.utils.log.RequireDebugFalse'}}, 'version': 1,
           'handlers': {'stream': {'level': 'WARNING', 'filters': ['require_debug_false'], 'class': 'logging.StreamHandler'},
                        'mail_admins': {'level': 'ERROR', 'min_interval': 600, 'filters': ['require_debug_false'], 'class': 'djangofloor.log.FloorAdminEmailHandler'}},
           'disable_existing_loggers': False}
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/accounts/login/'
LOGOUT_URL = '/accounts/logout/'
LOG_PATH = 'django_data/log'
MANAGERS = [['admin', 'admin@localhost']]
MAX_REQUESTS = 10000
MEDIA_ROOT = 'django_data/data/media'
MEDIA_URL = '/media/'
MIDDLEWARE_CLASSES = ['django.middleware.cache.UpdateCacheMiddleware', 'django.middleware.common.CommonMiddleware', 'debug_toolbar.middleware.DebugToolbarMiddleware',
                      'django.contrib.sessions.middleware.SessionMiddleware', 'django.middleware.csrf.CsrfViewMiddleware', 'django.middleware.security.SecurityMiddleware',
                      'django.contrib.auth.middleware.AuthenticationMiddleware', 'django.contrib.messages.middleware.MessageMiddleware', 'django.middleware.clickjacking.XFrameOptionsMiddleware',
                      'djangofloor.middleware.IEMiddleware', 'djangofloor.middleware.RemoteUserMiddleware', 'djangofloor.middleware.BasicAuthMiddleware',
                      'djangofloor.middleware.FakeAuthenticationMiddleware', 'django.middleware.cache.FetchFromCacheMiddleware']
OTHER_ALLAUTH = []
PIPELINE_CSS = {'default': {'source_filenames': ['bootstrap3/css/bootstrap.min.css', 'css/font-awesome.min.css'], 'extra_context': {'media': 'all'}, 'output_filename': 'css/default.css'}}
PIPELINE_CSS_COMPRESSOR = 'djangofloor.middleware.RCSSMinCompressor'
PIPELINE_JS = {'default': {'source_filenames': ['js/jquery.min.js', 'bootstrap3/js/bootstrap.min.js', 'js/djangofloor.js', 'js/ws4redis.js'], 'output_filename': 'js/default.js'},
               'ie9': {'source_filenames': ['js/html5shiv.js', 'js/respond.min.js'], 'output_filename': 'js/ie9.js'}}
PIPELINE_JS_COMPRESSOR = 'pipeline.compressors.jsmin.JSMinCompressor'
PIPELINE_MIMETYPES = [['text/coffeescript', '.coffee'], ['text/less', '.less'], ['text/javascript', '.js'], ['text/x-sass', '.sass'], ['text/x-scss', '.scss']]
PROJECT_NAME = 'moneta'
PROJECT_SETTINGS_MODULE_NAME = 'moneta.defaults'
REDIS_HOST = 'localhost'
REDIS_PORT = '6379'
REPOSITORY_CLASSES = [
    'moneta.repositories.aptitude.Aptitude',
    'moneta.repositories.pypi.Pypi',
    'moneta.repositories.maven3.Maven3',
    'moneta.repositories.flat_files.FlatFile',
    'moneta.repositories.yum.Yum',
]
REVERSE_PROXY_ACCESS_LOG_FILE = 'django_data/log/access.log'
REVERSE_PROXY_ERROR_LOG_FILE = 'django_data/log/error.log'
REVERSE_PROXY_IPS = ['127.0.0.1']
REVERSE_PROXY_PORT = None
REVERSE_PROXY_SSL_CRT_FILE = None
REVERSE_PROXY_SSL_KEY_FILE = None
REVERSE_PROXY_TIMEOUT = 30
ROOT_URLCONF = 'djangofloor.root_urls'
SECRET_KEY = 'NEZ6ngWX0JihNG2wepl1uxY7bkPOWrTEo27vxPGlUM3eBAYfPT'
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ['HTTP_X_FORWARDED_PROTO', 'https']
SECURE_SSL_REDIRECT = False
SERVER_EMAIL = 'root@localhost'
SERVER_NAME = 'localhost'
SESSION_COOKIE_SECURE = False
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SITE_ID = 1
STATICFILES_DIRS = []
STATICFILES_FINDERS = ['django.contrib.staticfiles.finders.AppDirectoriesFinder', 'django.contrib.staticfiles.finders.FileSystemFinder', 'pipeline.finders.PipelineFinder']
STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'
STATIC_ROOT = 'django_data/static'
STATIC_URL = '/static/'
STORAGES = {'archive': {'ROOT': 'django_data/storage/archives', 'ENGINE': 'moneta.repository.storages.FlatStorage', 'PATH_LEN': 1},
            'cache': {'ROOT': 'django_data/storage/cache', 'ENGINE': 'moneta.repository.storages.FlatStorage', 'PATH_LEN': 1},
            'default': {'ROOT': 'django_data/storage/uncompressed', 'ENGINE': 'moneta.repository.storages.FlatStorage', 'PATH_LEN': 1}}
STORAGE_ARCHIVE = 'archive'
STORAGE_CACHE = 'cache'
STORAGE_UNCOMPRESSED = 'uncompressed'
TEMPLATE_CONTEXT_PROCESSORS = ['django.contrib.auth.context_processors.auth', 'django.core.context_processors.debug', 'django.core.context_processors.request', 'django.core.context_processors.i18n',
                               'django.core.context_processors.media', 'django.core.context_processors.static', 'django.core.context_processors.tz',
                               'django.contrib.messages.context_processors.messages', 'djangofloor.context_processors.context_base', 'moneta.context_processors.context_base', ]
TEMPLATE_DEBUG = False
TEMPLATE_DIRS = ['django_data/templates']
TEMPLATE_LOADERS = ['django.template.loaders.filesystem.Loader', 'django.template.loaders.app_directories.Loader']
TEMP_ROOT = 'django_data/tmp'
TEST_RUNNER = 'django.test.runner.DiscoverRunner'
THREADS = 1
TIME_ZONE = 'Europe/Paris'
UPLOAD_ROOT = 'uploads'
USER_SETTINGS_PATH = 'django_data/etc/moneta/settings.py'
USE_CELERY = False
USE_I18N = True
USE_L10N = True
USE_SCSS = False
USE_TZ = True
USE_X_FORWARDED_HOST = True
USE_X_SEND_FILE = False
WEBSOCKET_URL = '/ws/'
WORKERS = 1
WS4REDIS_CONNECTION = {'db': 15, 'host': 'localhost', 'port': '6379'}
WS4REDIS_EMULATION_INTERVAL = 0
WS4REDIS_EXPIRE = 0
WS4REDIS_PREFIX = 'ws'
WS4REDIS_SUBSCRIBER = 'djangofloor.df_ws4redis.Subscriber'
WSGI_APPLICATION = 'djangofloor.wsgi_http.application'
X_ACCEL_REDIRECT = []
X_FRAME_OPTIONS = 'DENY'
