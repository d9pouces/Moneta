# coding=utf-8
from bootstrap3.templatetags.bootstrap3 import get_pagination_context
from django import template
from django.core.urlresolvers import reverse
from django.http import HttpRequest
from moneta.repository.models import Element, Repository

register = template.Library()


@register.filter
def extra_repo_urls(repo, request):
    return repo.get_model().extra_index_urls(request, repo)


@register.filter
def moneta_url(repo, view_name='index'):
    if repo.is_private:
        return 'authb-%s:%s' % (repo.archive_type, view_name)
    return '%s:%s' % (repo.archive_type, view_name)


@register.filter
def checksum(element, value):
    if element.repository.is_private:
        return reverse('moneta.views.get_checksum', kwargs={'eid': element.id, 'value': value})
    return reverse('moneta.views.get_checksum_p', kwargs={'eid': element.id, 'value': value})


@register.filter
def direct_link(element):
    if element.repository.is_private:
        return reverse('moneta.views.get_file', kwargs={'eid': element.id, 'name': element.filename})
    return reverse('moneta.views.get_file_p', kwargs={'eid': element.id, 'name': element.filename})


@register.filter
def signature(signature_, element=None):
    if element is None:
        element = signature_.element
    if element.repository.is_private:
        return reverse('moneta.views.get_signature', kwargs={'eid': element.id, 'sid': signature_.id})
    return reverse('moneta.views.get_signature_p', kwargs={'eid': element.id, 'sid': signature_.id})


@register.filter
def curl(repo):
    if repo.is_private:
        return 'curl -u : --anyauth'
    return 'curl'

@register.filter
def auth_moneta_url(repo, view_name='index'):
    return 'auth-%s:%s' % (repo.archive_type, view_name)


@register.inclusion_tag('bootstrap3/pagination.html')
def bootstrap_pagination_extra(page, search=None):
    """
    Render pagination for a page

    **Tag name**::

        bootstrap_pagination

    **Parameters**:

        :page:
        :kwargs:

    **usage**::

        {% bootstrap_pagination FIXTHIS %}

    **example**::

        {% bootstrap_pagination FIXTHIS %}
    """

    pagination_kwargs = {'extra': 'search=%s' % search, 'page': page}
    return get_pagination_context(**pagination_kwargs)