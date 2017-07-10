from djangofloor.conf.config_values import AutocreateDirectory, CallableSetting
from moneta.log import moneta_log_configuration

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

STORAGES = {
    'archive': {
        'ENGINE': 'moneta.repository.storages.FlatStorage',
        'ROOT': AutocreateDirectory('{MEDIA_ROOT}/archives'),
        'PATH_LEN': 1,
    },
    'default': {
        'ENGINE': 'moneta.repository.storages.FlatStorage',
        'ROOT': AutocreateDirectory('{MEDIA_ROOT}/uncompressed'),
        'PATH_LEN': 1,
    },
    'cache': {
        'ENGINE': 'moneta.repository.storages.FlatStorage',
        'ROOT': AutocreateDirectory('{MEDIA_ROOT}/cache'),
        'PATH_LEN': 1,
    }
}

STORAGE_ARCHIVE = 'archive'
STORAGE_UNCOMPRESSED = 'uncompressed'
STORAGE_CACHE = 'cache'
WEBSOCKET_URL = None

# TO BE CONFIGURED
GNUPG_HOME = AutocreateDirectory('{LOCAL_PATH}/gpg')
GNUPG_HOME_HELP = 'Path of the GnuPG secret data'
# TO BE CONFIGURED
TEMP_ROOT = AutocreateDirectory('{LOCAL_PATH}/tmp')
TEMP_ROOT_HELP = 'Path used for temporary archive storage'
# TO BE CONFIGURED
GNUPG_KEYID = '1DA759EA7F5EF06F'
GNUPG_KEYID_HELP = 'ID of the GnuPG key'
# TO BE CONFIGURED
GNUPG_PATH = 'gpg'
GNUPG_PATH_HELP = 'Path of the gpg binary'

LOGGING = CallableSetting(moneta_log_configuration)
