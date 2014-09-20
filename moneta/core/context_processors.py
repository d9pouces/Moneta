#coding=utf-8

from django.utils.six import u

__author__ = u('flanker')


def context_base(request):
    is_os_x = 'macintosh' in request.META.get('HTTP_USER_AGENT', '').lower()
    is_linux = 'linux' in request.META.get('HTTP_USER_AGENT', '').lower()
    absolute_url = request.build_absolute_uri('/')[:-1]
    return {'absolute_url': absolute_url, 'use_https': absolute_url.startswith('https'),
            'is_linux': is_linux, 'is_os_x': is_os_x}
