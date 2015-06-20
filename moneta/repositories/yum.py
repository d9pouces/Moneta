# -*- coding: utf-8 -*-
import json
import tempfile
import time

from django.conf import settings
from django.conf.urls import url
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
# noinspection PyPackageRequirements
from django.utils.translation import ugettext as _

from moneta.repositories.aptitude import Aptitude
from moneta.repositories import rpm
from moneta.repository.models import Repository, storage, Element, ArchiveState
from moneta.repository.signing import GPGSigner
from moneta.views import sendpath

__author__ = 'flanker'


class Yum(Aptitude):
    verbose_name = _('YUM repository for Linux .rpm packages')
    storage_uid = 'a87172de-0000-0000-0000-%012d'
    archive_type = 'yum'
    index_html = 'repositories/yum/index.html'

    def is_file_valid(self, uploaded_file):
        if not uploaded_file.name.endswith('.rpm'):
            return False
        try:
            rpm.RPM(uploaded_file.file)
        except rpm.RPMError:
            return False
        return True

    def update_element(self, element):
        fd = storage(settings.STORAGE_ARCHIVE).get_file(element.archive_key, sub_path='')
        rpm_obj = rpm.RPM(fd)
        element.filename = rpm_obj.canonical_filename
        element.version = rpm_obj.header.version
        element.archive = rpm_obj.header.name
        header = {}
        signature = {}
        for (obj_dict, header_base) in ((header, rpm_obj.header), (signature, rpm_obj.signature)):
            available = {}
            for entry in header_base:
                available[entry.tag] = entry.value
            for attr_name, infos in header_base.TAGS.items():
                attr_value = available.get(infos[0], infos[1])
                if not isinstance(attr_value, bytes):
                    obj_dict[attr_name] = attr_value
        rpm_ = {'binary': rpm_obj.binary, 'canonical_filename': rpm_obj.canonical_filename,
                'checksum': rpm_obj.checksum, 'filesize': rpm_obj.filesize, 'source': rpm_obj.source,
                'filelist': [{'type': x.type, 'name': x.name, } for x in rpm_obj.filelist],
                'provides': [{'name': x.name, 'str_flags': x.str_flags, 'version': list(x.version)} for x in rpm_obj.provides],
                'requires': [{'name': x.name, 'str_flags': x.str_flags, 'version': list(x.version)} for x in rpm_obj.requires],
                'changelog': [{'name': x.name, 'time': x.time, 'text': x.text, } for x in rpm_obj.changelog],
                'obsoletes': [{'name': x.name, 'str_flags': x.str_flags, 'version': list(x.version)} for x in rpm_obj.obsoletes],
                'conflicts': [{'name': x.name, 'str_flags': x.str_flags, 'version': list(x.version)} for x in rpm_obj.conflicts],
                'header_range': list(rpm_obj.header.header_range),
                }
        rpm_dict = {'header': header, 'signature': signature, 'rpm': rpm_, }
        element.extra_data = json.dumps(rpm_dict)

    def public_url_list(self):
        """
        Return a list of URL patterns specific to this repository
        Sample recognized urls:
            * /1/pool/repo_apt/stable/[package-1.0.0-amd64.deb]
            * /1/dists/repo_apt/Release[.gpg]
            * /1/dists/repo_apt/Contents-amd64.gz
            * /1/dists/repo_apt/stable/Release.xz
            * /1/dists/repo_apt/stable/binary-amd64/Packages.gz
            * /1/dists/repo_apt/stable/binary-amd64/Release.bz2
            * /1/keys/repo_apt/key.asc

        :return: a patterns as expected by django

        """
        pattern_list = [
            url(r'^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]+)/(?P<state_slug>[\w\-\._]+)/(?P<folder>[\w\-\._]+)/Packages/'
                r'(?P<filename>[\w\-\.]+)$', self.wrap_view('get_file'), name='get_file'),
            url(r'^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]+)/(?P<state_slug>[\w\-\._]+)/(?P<arch>[\w\-\._]+)/repodata/'
                r'(?P<filename>\w+\.xml)(?P<compression>|.bz2|.gz)$', self.wrap_view('repodata_file'), name='repodata_file'),
            url(r'^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]+)/(?P<state_slug>[\w\-\._]+)/(?P<arch>[\w\-\._]+)$',
                self.wrap_view('index'), name='repo_index'),
            url(r"^(?P<rid>\d+)/gpg_key.asc$", self.wrap_view('gpg_key'), name="gpg_key"),
            url(r"^(?P<rid>\d+)/$", self.wrap_view('index'), name="index"),
        ]
        return pattern_list

    def gpg_key(self, request, rid, repo_slug=None, slug=None):
        get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.archive_type)
        signature = GPGSigner().export_key()
        # noinspection PyUnusedLocal
        repo_slug, slug = slug, repo_slug
        return HttpResponse(signature, content_type="text/plain")

    def repodata_file(self, request, rid, repo_slug, state_slug, arch, filename, compression):
        if filename not in ('comps.xml', 'primary.xml', 'other.xml', 'filelists.xml', 'repomd.xml', ):
            return HttpResponse(_('File not found'), status=404)
        if compression and filename == 'repomd.xml':
            return HttpResponse(_('File not found'), status=404)
        # noinspection PyUnusedLocal
        repo_slug = repo_slug
        filename = self.index_filename(state_slug, arch, filename + compression)
        mimetype = 'text/xml'
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.archive_type)
        uid = self.storage_uid % repo.id
        key = storage(settings.STORAGE_CACHE).uid_to_key(uid)
        return sendpath(settings.STORAGE_CACHE, key, filename, mimetype)

    def generate_indexes(self, repository, states=None, validity=365):
        if states is None:
            states = list(ArchiveState.objects.filter(repository=repository).order_by('name'))
        revision = int(time.time())
        architectures_by_state = {x.slug: set() for x in states}  # architectures_by_state[archive_state.slug] = {'x86_64', 'c7', }
        # load all dict infos and count all architectures
        rpm_objects = []
        package_count_by_state_arch = {x.slug: {'noarch': 0} for x in states}
        for element in Element.objects.filter(repository=repository).prefetch_related('states'):
            rpm_dict = json.loads(element.extra_data)
            rpm_objects.append(rpm_dict)
            rpm_dict['states'] = [s.slug for s in element.states.all()]
            package_architecture = rpm_dict['header']['architecture'] or 'noarch'
            if package_architecture != 'noarch':
                for state_slug in rpm_dict['states']:
                    architectures_by_state[state_slug].add(package_architecture)
            for state_slug in rpm_dict['states']:
                package_count_by_state_arch[state_slug].setdefault(package_architecture, 0)
                package_count_by_state_arch[state_slug][package_architecture] += 1

        # add the count of 'noarch' packages to other architectures
        for state_slug, package_count_by_arch in package_count_by_state_arch.items():
            if len(package_count_by_arch) == 1:  # only 'noarch' architecture
                package_count_by_arch['x86_64'] = 0
                architectures_by_state[state_slug] = {'x86_64', }
            noarch_count = package_count_by_arch['noarch']
            del package_count_by_arch['noarch']
            for architecture in package_count_by_arch:
                package_count_by_arch[architecture] += noarch_count

        # prepare all files
        open_files = {}
        for state_slug, architectures in architectures_by_state.items():
            for architecture in architectures:
                def write(name_, data):
                    filename_ = self.index_filename(state_slug, architecture, name_)
                    open_files[filename_].write(data.encode('utf-8'))
                for name in ('other.xml', 'filelists.xml', 'comps.xml', 'primary.xml', ):

                    filename = self.index_filename(state_slug, architecture, name)
                    open_files[filename] = tempfile.TemporaryFile(mode='w+b', dir=settings.TEMP_ROOT)
                    write(name, '<?xml version="1.0" encoding="UTF-8"?>\n')
                package_count = package_count_by_state_arch[state_slug][architecture]
                write('other.xml', '<otherdata xmlns="http://linux.duke.edu/metadata/other" packages="%d">\n' % package_count)
                write('filelists.xml', '<filelists xmlns="http://linux.duke.edu/metadata/filelists" packages="%d">\n' % package_count)
                write('comps.xml', '<!DOCTYPE comps PUBLIC "-//CentOS//DTD Comps info//EN" "comps.dtd">\n')
                write('comps.xml', '<comps>\n')
                write('primary.xml', '<metadata xmlns="http://linux.duke.edu/metadata/common" xmlns:rpm="http://linux.duke.edu/metadata/rpm" packages="%d">\n' % package_count)
        # fill all files with RPMs
        for rpm_dict in rpm_objects:
            filelists = render_to_string('repositories/yum/filelists.xml', rpm_dict)
            primary = render_to_string('repositories/yum/primary.xml', rpm_dict)
            other = render_to_string('repositories/yum/other.xml', rpm_dict)
            for state_slug in rpm_dict['states']:
                architectures = {rpm_dict['header']['architecture'], }
                if architectures == {'noarch', }:
                    architectures = architectures_by_state[state_slug]
                for architecture in architectures:
                    open_files[self.index_filename(state_slug, architecture, 'filelists.xml')].write(filelists.encode('utf-8'))
                    open_files[self.index_filename(state_slug, architecture, 'primary.xml')].write(primary.encode('utf-8'))
                    open_files[self.index_filename(state_slug, architecture, 'other.xml')].write(other.encode('utf-8'))
        # finish all files
        for state_slug, architectures in architectures_by_state.items():
            for architecture in architectures:
                open_files[self.index_filename(state_slug, architecture, 'other.xml')].write(b'</otherdata>')
                open_files[self.index_filename(state_slug, architecture, 'filelists.xml')].write(b'</filelists>')
                open_files[self.index_filename(state_slug, architecture, 'comps.xml')].write(b'</comps>')
                open_files[self.index_filename(state_slug, architecture, 'primary.xml')].write(b'</metadata>')

        storage_uid = self.storage_uid % repository.id
        # generate a compressed version of each file
        list_of_hashes = self.compress_files(open_files, '', storage_uid)
        dict_of_hashes = {x[0]: x for x in list_of_hashes}
        for state_slug, architectures in architectures_by_state.items():
            for architecture in architectures:
                filename = self.index_filename(state_slug, architecture, 'repomd.xml')
                open_files[filename] = tempfile.TemporaryFile(mode='w+b', dir=settings.TEMP_ROOT)
                other = self.index_filename(state_slug, architecture, 'other.xml')
                filelists = self.index_filename(state_slug, architecture, 'filelists.xml')
                comps = self.index_filename(state_slug, architecture, 'comps.xml')
                primary = self.index_filename(state_slug, architecture, 'primary.xml')
                template_values = {'revision': revision,
                                   'other': dict_of_hashes[other],
                                   'filelists': dict_of_hashes[filelists],
                                   'comps': dict_of_hashes[comps],
                                   'primary': dict_of_hashes[primary],
                                   'other_gz': dict_of_hashes[other + '.gz'],
                                   'filelists_gz': dict_of_hashes[filelists + '.gz'],
                                   'comps_gz': dict_of_hashes[comps + '.gz'],
                                   'primary_gz': dict_of_hashes[primary + '.gz'], }
                repomd = render_to_string('repositories/yum/repomd.xml', template_values)
                repomd_file = open_files[filename]
                repomd_file.write(repomd.encode('utf-8'))
                repomd_file.flush()
                repomd_file.seek(0)
                storage(settings.STORAGE_CACHE).store_descriptor(storage_uid, filename, repomd_file)

    @staticmethod
    def index_filename(state: str, architecture: str, name: str):
        return '%(state)s/%(architecture)s/repodata/%(name)s' % {'state': state, 'architecture': architecture, 'name': name, }
