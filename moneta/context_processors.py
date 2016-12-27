# coding=utf-8
from django.conf import settings
from moneta import __version__ as version

__author__ = 'flanker'


def context_base(request):
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    is_os_x = 'macintosh' in user_agent
    is_linux = 'linux' in user_agent
    absolute_url = settings.SERVER_BASE_URL[:-1]
    return {'absolute_url': absolute_url, 'use_https': absolute_url.startswith('https'),
            'is_linux': is_linux, 'is_os_x': is_os_x, 'moneta_version': version, 'server_name': settings.SERVER_NAME, }
