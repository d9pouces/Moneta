# coding=utf-8
from django.contrib import messages
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _


def public_check(request):
    messages.success(request, _('You can access to this page.'))
    return render_to_response('core/empty.html', RequestContext(request))


def private_check(request):
    if request.user.is_anonymous():
        messages.error(request, _('You are not authenticated.'))
    else:
        messages.success(request, _('You can access to this page and you are authenticated.'))
    return render_to_response('core/empty.html', RequestContext(request))
