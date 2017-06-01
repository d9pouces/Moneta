# -*- coding: utf-8 -*-
"""Emulate a Jetbrains repository.

"""
from django.conf.urls import url
from django.urls import reverse
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _

from moneta.repositories.base import RepositoryModel
from moneta.repository.models import Repository, ArchiveState, Element
from moneta.templatetags.moneta import moneta_url

__author__ = 'Matthieu Gallet'


class Jetbrains(RepositoryModel):
    verbose_name = _('Jetbrains repository for IDEs')
    storage_uid = 'jetbrain-0000-0000-0000-%012d'
    archive_type = 'jetbrains'
    index_html = 'repositories/jetbrains/index.html'

    def public_url_list(self):
        return [
            url(r"^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]*)/s/(?P<state_slug>[\w\-\._]+)/updatePlugins.xml$",
                self.wrap_view('plugin_index'), name='plugin_index'),
            url(r"^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]*)/a/updatePlugins.xml$", self.wrap_view('plugin_index'),
                name='plugin_index'),
            url(r"^(?P<rid>\d+)/$", self.wrap_view('index'), name="index"),
        ]

    def plugin_index(self, request: HttpRequest, rid, repo_slug, state_slug=None):
        # noinspection PyUnusedLocal
        repo_slug = repo_slug
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.archive_type)
        base_query = Element.objects.filter(repository=repo)
        if state_slug:
            state = get_object_or_404(ArchiveState, repository=repo, name=state_slug)
            base_query = base_query.filter(states=state)
        return TemplateResponse(request, 'repositories/jetbrains/updatePlugins.xml', {'elements': base_query},
                                content_type='application/xml')

    def index(self, request, rid):
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.archive_type)
        states = [state for state in ArchiveState.objects.filter(repository=repo).order_by('name')]
        tab_infos = [(reverse('repositories:jetbrains:plugin_index', kwargs={'rid': repo.id, 'repo_slug': repo.slug}),
                      ArchiveState(name=_('All states'), slug='all-states'), states), ]
        tab_infos += [(reverse('repositories:jetbrains:plugin_index',
                               kwargs={'rid': repo.id, 'repo_slug': repo.slug, 'state_slug': state.slug}),
                       state, [state])
                      for state in states]

        template_values = {'repo': repo, 'states': states, 'upload_allowed': repo.upload_allowed(request),
                           'index_url': reverse(moneta_url(repo, 'index'), kwargs={'rid': repo.id, }),
                           'tab_infos': tab_infos, 'admin_allowed': repo.admin_allowed(request), }
        return TemplateResponse(request, self.index_html, template_values)


if __name__ == '__main__':
    import doctest

    doctest.testmod()
