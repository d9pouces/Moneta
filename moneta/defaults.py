from djangofloor.conf.config_values import Directory, CallableSetting, AutocreateFileContent
from moneta.conf import moneta_log_configuration, auto_generate_signing_key

__author__ = 'flanker'

DF_TEMPLATE_CONTEXT_PROCESSORS = ['moneta.context_processors.context_base']
DF_INDEX_VIEW = 'moneta.views.index'
DF_INSTALLED_APPS = ['moneta', 'moneta.repositories', 'moneta.repository', ]
DF_SITE_SEARCH_VIEW = None
DF_URL_CONF = 'moneta.root_urls.urls'
LISTEN_ADDRESS = '127.0.0.1:8131'
SERVER_BASE_URL = 'http://localhost:8131/'
USE_CELERY = False
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
    'moneta.repositories.vagrant.Vagrant',
]
USE_HTTP_BASIC_AUTH = True

STORAGES = {
    'archive': {
        'ENGINE': 'moneta.repository.storages.FlatStorage',
        'ROOT': Directory('{MEDIA_ROOT}/archives'),
        'PATH_LEN': 1,
    },
    'default': {
        'ENGINE': 'moneta.repository.storages.FlatStorage',
        'ROOT': Directory('{MEDIA_ROOT}/uncompressed'),
        'PATH_LEN': 1,
    },
    'cache': {
        'ENGINE': 'moneta.repository.storages.FlatStorage',
        'ROOT': Directory('{MEDIA_ROOT}/cache'),
        'PATH_LEN': 1,
    }
}

STORAGE_ARCHIVE = 'archive'
STORAGE_UNCOMPRESSED = 'uncompressed'
STORAGE_CACHE = 'cache'
WEBSOCKET_URL = None

GNUPG_HOME = Directory('{LOCAL_PATH}/gpg')
GNUPG_KEYID = AutocreateFileContent('{LOCAL_PATH}/gpg_key_id.txt', auto_generate_signing_key)
GNUPG_PATH = 'gpg'

LOGGING = CallableSetting(moneta_log_configuration)
