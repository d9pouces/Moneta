# -*- coding: utf-8 -*-
# https://www.nopsec.com/news-and-resources/blog/2015/3/27/private-vagrant-box-hosting-easy-versioning/
import json
import tarfile

from django.conf import settings
from django.conf.urls import url
from django.core.files.uploadedfile import UploadedFile
from django.urls import reverse
from django.http import HttpRequest
from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _

from moneta.repositories.base import RepositoryModel
from moneta.repository.models import ArchiveState, Element, storage
from moneta.repository.models import Repository
from moneta.templatetags.moneta import moneta_url
from moneta.views import get_file

__author__ = 'Matthieu Gallet'


class Vagrant(RepositoryModel):
    verbose_name = _('Vagrant custom box catalog')
    storage_uid = 'vagrant-0000-0000-0000-%012d'
    archive_type = 'vagrant'
    index_html = 'repositories/vagrant/index.html'

    def is_file_valid(self, uploaded_file: UploadedFile):
        name = uploaded_file.name
        if not name.endswith('.box'):
            return False
        # noinspection PyBroadException
        try:
            tarfile.open(fileobj=uploaded_file.file, mode='r', name=None)
        except Exception:
            return False
        return True

    def update_element(self, element):
        """
        Extract some informations from element to prepare the repository
        :param element: Element to add to the repository
        :return: Unicode string containing meta-data
        """
        if element.archive:
            element.name = element.archive.rpartition('.')[2]
        archive_file = storage(settings.STORAGE_ARCHIVE).get_file(element.archive_key)
        compressed_file = tarfile.open(name=None, fileobj=archive_file, mode='r')
        all_names = {x for x in compressed_file.getnames()}
        provider = 'virtualbox'
        if 'metadata.json' in all_names:
            metadata_file = compressed_file.extractfile('metadata.json')
            metadata = json.loads(metadata_file.read().decode('utf-8'))
            provider = metadata['provider']
        element.extra_data = json.dumps({'provider': provider})

    def finish_element(self, element: Element, states: list):
        """
        Called after the .save() operations, with all states associated to this new element.
        Remove previous versions from target states
        :param element: Element
        :param states: list of ArchiveState
        """
        # remove previous versions from the given states:
        # noinspection PyUnresolvedReferences
        Element.states.through.objects.exclude(element__version=element.version) \
            .filter(archivestate__in=states, element__archive=element.archive).delete()
        super().finish_element(element, states)

    def public_url_list(self):
        # vagrant.org.com/org/base-trusty64.json
        # vagrant.org.com/org/base-trusty64/version/1.0.0/virtualbox/base-trusty64-1.0.0-virtualbox.json

        return [
            # https://atlas.hashicorp.com/bento/boxes/centos-7.1/versions/2.2.2/providers/vmware_desktop.box
            url(r"^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]+)/boxes/(?P<eid>\d+)-(?P<archive>[\w\-\._]+)/"
                r"versions/(?P<version>[\w\-\._]+)/providers/(?P<provider>[\w\-\._]+)\.box",
                self.wrap_view('get_box'), name='get_box'),
            url(r"^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]*)/s/(?P<state_slug>[\w\-\._]+)/(?P<archive>[^/]+)\.json$",
                self.wrap_view('archive_json'), name='archive_json'),
            url(r"^(?P<rid>\d+)/s(?P<state_slug>[\w\-\._]*)\.html$", self.wrap_view('index'), name="index"),
            url(r"^(?P<rid>\d+)\.html$", self.wrap_view('index'), name="index"),
        ]

    def get_box(self, request: HttpRequest, rid, repo_slug, eid, archive, version, provider):
        # noinspection PyUnusedLocal
        repo_slug = repo_slug
        # noinspection PyUnusedLocal
        archive = archive
        # noinspection PyUnusedLocal
        provider = provider
        # noinspection PyUnusedLocal
        version = version
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.archive_type)
        elements = list(Element.objects.filter(repository=repo, pk=eid)[0:1])
        if not elements:
            return JsonResponse({'errors': ['Not found', ], })
        return get_file(request, eid, element=elements[0])

    def archive_json(self, request: HttpRequest, rid, repo_slug, state_slug=None, archive=None):
        # noinspection PyUnusedLocal
        repo_slug = repo_slug
        result = self.get_providers_by_version(request, rid, state_slug, archive)
        return JsonResponse(result)

    # noinspection PyUnusedLocal
    def index(self, request, rid, repo_slug=None, state_slug=''):
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.archive_type)
        base_query = Element.objects.filter(repository=repo)
        if state_slug:
            state = get_object_or_404(ArchiveState, repository=repo, name=state_slug)
            base_query = base_query.filter(states=state)
        base_query = base_query.order_by('archive', 'version')
        element_infos = []
        for element in base_query:
            if not element.extra_data:
                continue
            provider = json.loads(element.extra_data)['provider']
            element_infos.append(
                (element.name,
                 reverse('repositories:vagrant:get_box',
                         kwargs={'rid': rid, 'repo_slug': repo.slug, 'eid': element.id, 'provider': provider,
                                 'archive': element.archive, 'version': element.version}),
                 element.sha1)
            )
        states = [state for state in ArchiveState.objects.filter(repository=repo).order_by('name')]
        tab_infos = []
        # list of (relative URL, name, list of states, state_slug)
        tab_infos += [(reverse('repositories:vagrant:index',
                               kwargs={'rid': repo.id, 'state_slug': state.slug}),
                       state, [state], state.slug)
                      for state in states]
        tab_infos += [(reverse('repositories:vagrant:index', kwargs={'rid': repo.id, 'state_slug': ''}),
                      ArchiveState(name=_('All boxes'), slug='all-states'), states, ''), ]

        template_values = {'repo': repo, 'states': states, 'upload_allowed': repo.upload_allowed(request),
                           'state_slug': state_slug, 'elements': element_infos,
                           'index_url': reverse(moneta_url(repo, 'index'), kwargs={'rid': repo.id, }),
                           'tab_infos': tab_infos, 'admin_allowed': repo.admin_allowed(request), }
        return TemplateResponse(request, self.index_html, template_values)

    def get_providers_by_version(self, request, rid, state_slug, archive):
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.archive_type)
        base_query = Element.objects.filter(repository=repo, archive=archive)
        if state_slug:
            state = get_object_or_404(ArchiveState, repository=repo, name=state_slug)
            base_query = base_query.filter(states=state)
        versions = {}
        for element in base_query:
            metadata = json.loads(element.extra_data)
            versions.setdefault(element.version, []).append({
                'name': metadata['provider'],
                'url': '%s%s' % (settings.SERVER_BASE_URL[:-1], element.get_direct_link()),
                'checksum_type': 'sha1',

                'checksum': element.sha1})
        result = {'name': archive, 'description': _('This box contains %(name)s') % {'name': archive},
                  'versions': [{'version': k, 'status': 'active', 'providers': v} for (k, v) in versions.items()]}
        return result
# Vagrant.configure(2) do |config|
#
#   config.vm.box = "{$relativePathInfo|escape}"
#   config.vm.box_url = '<a href="{$CATALOG_URI|escape}{$pathInfo|escape}">{$CATALOG_URI|escape}{$pathInfo|escape}</a>'
#
#   # Whatever other config stuff you want to do
# end
