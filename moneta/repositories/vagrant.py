# -*- coding: utf-8 -*-
# https://www.nopsec.com/news-and-resources/blog/2015/3/27/private-vagrant-box-hosting-easy-versioning/
import os
import zipfile
from django.conf import settings

from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.http import HttpRequest
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _

from moneta.repositories.base import RepositoryModel
from moneta.repository.models import ArchiveState, Element, storage
from moneta.repository.models import Repository
from moneta.templatetags.moneta import moneta_url
from moneta.utils import parse_control_data


__author__ = 'Matthieu Gallet'


class Vagrant(RepositoryModel):
    verbose_name = _('Vagrant custom box catalog')
    storage_uid = 'vagrant-0000-0000-0000-%012d'
    archive_type = 'vagrant'
    index_html = 'repositories/vagrant/index.html'


    def is_file_valid(self, uploaded_file):
        name = uploaded_file.name
        for suffix in ('.tar.gz', '.zip', '.tar.xz', '.tar.bz2'):
            if name.endswith(suffix):
                return True
        return False

    def update_element(self, element):
        """
        Extract some informations from element to prepare the repository
        :param element: Element to add to the repository
        :return: Unicode string containing meta-data
        """
        if element.archive:
            element.name = element.archive.rpartition('.')[2]
        if element.filename.endswith('.zip'):
            archive_file = storage(settings.STORAGE_ARCHIVE).get_file(element.archive_key)

            compressed_file = zipfile.ZipFile(archive_file)
            metadata_file = compressed_file.extract('metadata.json')

            prefix = os.path.commonprefix(compressed_file.namelist())
            control_data_file = compressed_file.open(os.path.join(prefix, 'META-INF', 'MANIFEST.MF'))

            control_data_value = control_data_file.read().decode('utf-8')
            control_data_file.close()
            compressed_file.close()
            archive_file.close()
            element.extra_data = control_data_value
            control_data = parse_control_data(control_data_value, continue_line=' ')
            for key, attr in (('Bundle-SymbolicName', 'name'), ('Bundle-Version', 'version'),
                              ('Implementation-Title', 'archive'), ('Implementation-Version', 'version'),
                              ('Name', 'name'),):
                if key in control_data:  # archive : PackageName, name : Organization Name
                    setattr(element, attr, control_data.get(key, ''))
                    # element.filename = '%s-%s.jar' % (element.archive.rpartition('.')[2], element.version)

    def finish_element(self, element: Element, states: list):
        """
        Called after the .save() operations, with all states associated to this new element.
        :param element: Element
        :param states: list of ArchiveState
        """
        RepositoryModel.finish_element(self, element, states)

    def public_url_list(self):
        # vagrant.org.com/org/base-trusty64.json
        # vagrant.org.com/org/base-trusty64/version/1.0.0/virtualbox/base-trusty64-1.0.0-virtualbox.json

        return [
            url(r"^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]*)/s/(?P<state_slug>[\w\-\._]+)/(?P<archive>[^/]+)\.json$",
                self.wrap_view('archive_json'), name='archive_json'),
            url(r"^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]*)/s/(?P<state_slug>[\w\-\._]+)/(?P<archive>[^/]+)/"
                r"version/(?P<version>[^/]+)/(?P<provider>[^/]+)/(?P<name>^[/]+)\.json$",
                self.wrap_view('box_json'), name='box_json'),
            url(r"^(?P<rid>\d+)/$", self.wrap_view('index'), name="index"),
        ]

    def box_usage(self, request: HttpRequest, rid, repo_slug, state_slug=None, archive=None):
        pass

    def archive_json(self, request: HttpRequest, rid, repo_slug, state_slug=None, archive=None):
        pass

    def box_json(self, request: HttpRequest, rid, repo_slug, state_slug=None, archive=None, version=None,
                 provider=None, name=None):
        pass

    def index(self, request, rid):
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.archive_type)
        states = [state for state in ArchiveState.objects.filter(repository=repo).order_by('name')]
        tab_infos = [(reverse('jetbrains:plugin_index', kwargs={'rid': repo.id, 'repo_slug': repo.slug}),
                      ArchiveState(name=_('All states'), slug='all-states'), states), ]
        tab_infos += [(reverse('jetbrains:plugin_index', kwargs={'rid': repo.id, 'repo_slug': repo.slug, 'state_slug': state.slug}), state, [state])
                      for state in states]

        template_values = {'repo': repo, 'states': states, 'upload_allowed': repo.upload_allowed(request),
                           'index_url': reverse(moneta_url(repo, 'index'), kwargs={'rid': repo.id, }),
                           'tab_infos': tab_infos, 'admin_allowed': repo.admin_allowed(request), }
        return render_to_response(self.index_html, template_values, RequestContext(request))
# Vagrant.configure(2) do |config|
#
#   config.vm.box = "{$relativePathInfo|escape}"
#   config.vm.box_url = '<a href="{$CATALOG_URI|escape}{$pathInfo|escape}">{$CATALOG_URI|escape}{$pathInfo|escape}</a>'
#
#   # Whatever other config stuff you want to do
# end