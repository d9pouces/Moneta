# -*- coding: utf-8 -*-
import os
import tarfile
import zipfile

from django.conf import settings
from django.conf.urls import url
from django.core.files.uploadedfile import UploadedFile
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _
import requests

from moneta.exceptions import InvalidRepositoryException
from moneta.repositories.aptitude import Aptitude
from moneta.repositories.base import RepositoryModel
from moneta.repositories.pypi import PyArchive
from moneta.repository.models import ArchiveState, Element, Repository, storage
from moneta.templatetags.moneta import moneta_url
from moneta.utils import parse_control_data

__author__ = 'flanker'


class RubyGem(Aptitude):
    verbose_name = _('Gem repository for Ruby packages')
    storage_uid = '71610000-0000-0000-0000-%012d'
    archive_type = 'rubygem'

    def finish_element(self, element: Element, states: list):
        """
        Called after the .save() operations, with all states associated to this new element.
        :param element: Element
        :param states: list of ArchiveState
        """
        RepositoryModel.finish_element(self, element, states)

    def is_file_valid(self, uploaded_file: UploadedFile):
        return True

    @staticmethod
    def open_file(filename, archive_file):
        """ identify compression type and return a tuple (open compressed file, compression_type, prefix).
        If compression type is unknown, return None
        """
        endswith = filename.endswith
        compressed_file = None
        # noinspection PyBroadException
        try:
            if endswith('.tar.gz') or endswith('.tar.xz') or endswith('.tar.bz2'):
                compressed_file = tarfile.open(name='file.tar', mode='r:*', fileobj=archive_file)
                prefix = os.path.commonprefix(compressed_file.getnames())
                return PyArchive(compressed_file, 'tar', prefix)
            if endswith('.zip'):
                compressed_file = zipfile.ZipFile(archive_file)
                prefix = os.path.commonprefix(compressed_file.namelist())
                return PyArchive(compressed_file, 'zip', prefix)
            if endswith('.egg'):
                compressed_file = zipfile.ZipFile(archive_file)
                prefix = os.path.commonprefix(compressed_file.namelist())
                return PyArchive(compressed_file, 'egg', prefix)
            if endswith('.whl'):
                compressed_file = zipfile.ZipFile(archive_file)
                prefix = os.path.commonprefix(compressed_file.namelist())
                return PyArchive(compressed_file, 'whl', prefix)
        except Exception:
            if compressed_file:
                compressed_file.close()
        return None

    def update_element(self, element):
        """
        Extract some informations from element to prepare the repository
        :param element: Element to add to the repository
        :return: Unicode string containing meta-data

        ar -x control.tar.gz
        tar -xf control.tar.gz control
        """
        archive_file = storage(settings.STORAGE_ARCHIVE).get_file(element.archive_key)
        py_archive = self.open_file(element.filename, archive_file)
        if py_archive is None:
            raise InvalidRepositoryException(_('Unable to open file'))
        try:
            control_data_value = py_archive.get_pkg_info()
            if not control_data_value:
                raise InvalidRepositoryException(_('No control data in archive'))
            element.extra_data = control_data_value
            control_data = parse_control_data(control_data_value, continue_line='        ', skip_after_blank=True)
            for key, attr in (('Name', 'archive'), ('Version', 'version'), ('Home-page', 'official_link'),
                              ('Description', 'long_description')):
                if key in control_data:
                    setattr(element, attr, control_data.get(key, ''))
            element.archive = element.archive.replace('-', '').replace('_', '')
            element.name = element.archive
        finally:
            py_archive.close()
            archive_file.close()

    def public_url_list(self):
        """
        Return a list of URL patterns specific to this repository
        Sample recognized urls:
            *

        :return: a patterns as expected by django

        """
        pattern_list = [
            url(r"^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]*)/specs.4.8.gz$",
                self.wrap_view('simple'), name="specs"),

            url(r"^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]*)/s/(?P<state_slug>[\w\-\._]+)/simple/?$",
                self.wrap_view('simple'), name="simple"),
            url(r"^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]*)/s/(?P<state_slug>[\w\-\._]+)/simple/"
                "(?P<search_pattern>[a-z\d_\-]*)/?$", self.wrap_view('simple'),
                name="simple"),
            url(r"^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]*)/s/(?P<state_slug>[\w\-\._]+)/rpc/?$",
                self.wrap_view('xmlrpc', csrf_exempt=True), name="xmlrpc"),
            url(r"^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]*)/simple/?$", self.wrap_view('simple'), name="simple"),
            url(r"^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]*)/simple/(?P<search_pattern>[a-zA-Z\d_\-]*)/?$",
                self.wrap_view('simple'), name="simple"),
            url(r"^\d+/[\w\-\._]+/[\w\-\._]+/f/(?P<eid>\d+)/.*$", self.wrap_view('get_filename'), name="get_file"),
            url(r"^(?P<rid>\d+)/$", self.wrap_view('index'), name="index"),
            url(r"^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]*)/$", self.wrap_view('search_plugin'), name="search_plugin"),
            url(r"^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]*)/plugin/(?P<eid>\d+)$", self.wrap_view('search_plugin'), name="search_plugin"),
        ]
        return pattern_list

    def index(self, request, rid):
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.archive_type)
        states = list(ArchiveState.objects.filter(repository=repo).order_by('name'))
        template_values = {'repo': repo, 'states': states, 'upload_allowed': repo.upload_allowed(request),
                           'admin_allowed': repo.admin_allowed(request), }
        view_name = moneta_url(repo, 'simple')
        tab_infos = [
            (reverse(view_name, kwargs={'rid': repo.id, 'repo_slug': repo.slug}), states,
             ArchiveState(name=_('All states'), slug='all-states')),
        ]
        for state in states:
            tab_infos.append(
                (reverse(view_name, kwargs={'rid': repo.id, 'repo_slug': repo.slug, 'state_slug': state.slug}), [state], state)
            )
        template_values['tab_infos'] = tab_infos
        return render_to_response('repositories/pypi/index.html', template_values, RequestContext(request))

    def search_plugin(self, request, rid, repo_slug):
        for k, v in request.META.items():
            if k.startswith('HTTP'):
                print(k, v)
        r = requests.get('https://plugins.jetbrains.com/?build=PY-141.1245')
        print(r.text)
        return HttpResponse(r.text)

    @staticmethod
    def get_filename(request, eid):
        from moneta.views import get_file

        return get_file(request, eid)

    # noinspection PyUnusedLocal
    def simple(self, request, rid, repo_slug, state_slug=None, search_pattern=''):
        search_pattern = search_pattern.replace('-', '').replace('_', '')
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.archive_type)
        base_query = Element.objects.filter(repository=repo)
        if state_slug:
            state = get_object_or_404(ArchiveState, repository=repo, name=state_slug)
            base_query = base_query.filter(states=state)
        if search_pattern:
            base_query = base_query.filter(archive__iexact=search_pattern)
        view_name = moneta_url(repo, 'get_file')
        elements = [(x.filename, x.md5, reverse(view_name, kwargs={'eid': x.id, })) for x in base_query[0:1000]]
        template_values = {'elements': elements, 'rid': rid, }
        return render_to_response('repositories/pypi/simple.html', template_values, RequestContext(request))
