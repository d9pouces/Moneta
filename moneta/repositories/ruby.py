import base64
import gzip
import io
import json
import subprocess
import tarfile
import tempfile
import zlib
from distutils.version import LooseVersion

# noinspection PyPackageRequirements
import yaml
from django.conf import settings
from django.conf.urls import url
from django.core.files.uploadedfile import UploadedFile
from django.urls import reverse
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils.translation import gettext as _
from rubymarshal.classes import UsrMarshal
from rubymarshal.writer import write
# noinspection PyPackageRequirements
from yaml import MappingNode
# noinspection PyPackageRequirements
from yaml.composer import Composer
# noinspection PyPackageRequirements
from yaml.constructor import Constructor
# noinspection PyPackageRequirements
from yaml.parser import Parser
# noinspection PyPackageRequirements
from yaml.reader import Reader
# noinspection PyPackageRequirements
from yaml.resolver import Resolver
# noinspection PyPackageRequirements
from yaml.scanner import Scanner

from moneta.repositories.aptitude import Aptitude
from moneta.repositories.base import RepositoryModel
from moneta.repository.models import ArchiveState, Element, Repository, storage
from moneta.templatetags.moneta import moneta_url
from moneta.views import sendpath

__author__ = 'flanker'


class RubyMarshal(UsrMarshal):
    def __init__(self, values):
        super().__init__('Gem::' + self.__class__.__name__, values=values)


class Version(RubyMarshal):
    @property
    def version(self):
        return self.values['version']


class Specification(RubyMarshal):
    @property
    def name(self):
        return self.values['name']

    @property
    def version(self) -> Version:
        return self.values['version']

    @property
    def platform(self):
        return self.values['platform']

    @property
    def description(self):
        return self.values['description']

    @property
    def rubygems_version(self):
        return self.values['rubygems_version']

    @property
    def summary(self):
        return self.values['summary']


class Dependency(RubyMarshal):
    @property
    def name(self):
        return self.values['name']

    @property
    def requirement(self):
        return self.values['requirement']

    @property
    def type(self):
        return self.values['type']

    @property
    def prerelease(self):
        return self.values['prerelease']

    @property
    def version_requirements(self):
        return self.values['version_requirements']


class Requirement(RubyMarshal):
    @property
    def requirements(self):
        return self.values['requirements']


class RubyConstructor(Constructor):
    def construct_version(self, node, deep=False):
        if isinstance(node, MappingNode):
            self.flatten_mapping(node)
        return Version(super(RubyConstructor, self).construct_mapping(node, deep=deep))

    def construct_specification(self, node, deep=False):
        if isinstance(node, MappingNode):
            self.flatten_mapping(node)
        return Specification(super(RubyConstructor, self).construct_mapping(node, deep=deep))

    def construct_dependency(self, node, deep=False):
        if isinstance(node, MappingNode):
            self.flatten_mapping(node)
        return Dependency(super(RubyConstructor, self).construct_mapping(node, deep=deep))

    def construct_requirement(self, node, deep=False):
        if isinstance(node, MappingNode):
            self.flatten_mapping(node)
        return Requirement(super(RubyConstructor, self).construct_mapping(node, deep=deep))


RubyConstructor.add_constructor('!ruby/object:Gem::Specification', RubyConstructor.construct_specification)
RubyConstructor.add_constructor('!ruby/object:Gem::Version', RubyConstructor.construct_version)
RubyConstructor.add_constructor('!ruby/object:Gem::Dependency', RubyConstructor.construct_dependency)
RubyConstructor.add_constructor('!ruby/object:Gem::Requirement', RubyConstructor.construct_requirement)


class RubyLoader(Reader, Scanner, Parser, Composer, RubyConstructor, Resolver):
    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        RubyConstructor.__init__(self)
        Resolver.__init__(self)


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
        # self.generate_indexes(element.repository)

    def is_file_valid(self, uploaded_file: UploadedFile):
        if not uploaded_file.name.endswith('.gem'):
            return False
        try:
            fileobj = uploaded_file.file
            fd = tarfile.open(fileobj=fileobj, mode='r|')
            names = fd.getnames()
            fd.close()
        except tarfile.TarError:
            return False
        if 'data.tar.gz' not in names or 'metadata.gz' not in names:
            return False
        return True

    def update_element(self, element):
        """
        Extract some informations from element to prepare the repository
        :param element: Element to add to the repository
        :return: Unicode string containing meta-data

        ar -x control.tar.gz
        tar -xf control.tar.gz control
        """
        archive_file = storage(settings.STORAGE_ARCHIVE).get_file(element.archive_key, '')
        gem_fd = tarfile.open(fileobj=archive_file, mode='r')
        metadata_fd = gem_fd.extractfile('metadata.gz')
        metadata_gz_content = metadata_fd.read()
        metadata_bytes = gzip.decompress(metadata_gz_content)
        gem_fd.close()
        data = yaml.load(io.BytesIO(metadata_bytes), Loader=RubyLoader)
        for key, attr in (('name', 'archive'), ('homepage', 'official_link'), ('summary', 'long_description'),
                          ('name', 'name')):
            if key in data.values:
                setattr(element, attr, data.values[key])
        element.version = data.values['version'].version
        p = subprocess.Popen(['ruby', '-e', 'puts Marshal.dump (Gem::Specification.from_yaml(ARGF.read))'],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stdout, stderr = p.communicate(metadata_bytes)
        extra_data = {'yaml': metadata_bytes.decode('utf-8'), 'marshal': base64.b64encode(stdout).decode('utf-8')}
        element.extra_data = json.dumps(extra_data)

    @staticmethod
    def marshal_data(elt: Element) -> bytes:
        marshal = json.loads(elt.extra_data)['marshal']
        return base64.b64decode(marshal.encode('utf-8'))

    @staticmethod
    def python_data(elt: Element) -> Specification:
        data = json.loads(elt.extra_data)['yaml']
        return yaml.load(io.BytesIO(data.encode('utf-8')), Loader=RubyLoader)

    @staticmethod
    def yaml_data(elt: Element) -> Specification:
        return json.loads(elt.extra_data)['yaml']

    def public_url_list(self):
        """
        Return a list of URL patterns specific to this repository
        Sample recognized urls:
            *

        :return: a patterns as expected by django

        """
        src_pattern_list = [(r'(?P<filename>(specs\.4\.8|prerelease_specs\.4\.8|latest_specs\.4\.8|Marshal\.4\.8|'
                             r'versions\.list|names\.list)(\.gz)?)', 'specs', 'specs'),
                            (r'gems/(?P<filename>.+)', 'download', 'download'),
                            (r'specs/(?P<filename>.+)\.gemspec', 'gem_specs', 'gem_specs'),
                            (r'quick/Marshal\.4\.8/(?P<filename>.+)\.gemspec(?P<compression>(\.rz|))',
                             'quick_gem_specs', 'quick_gem_specs'),
                            (r'', 'index', 'index'),
                            ]
        pattern_list = []
        for pattern, view, name in src_pattern_list:
            pattern_list.append(
                url(r"^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]*)/a/%s$" % pattern, self.wrap_view(view), name=name)
            )
            pattern_list.append(
                url(r"^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]*)/s/(?P<state_slug>[\w\-\._]+)/%s$" % pattern,
                    self.wrap_view(view), name=name)
            )
        pattern_list += [
            url(r"^(?P<rid>\d+)/$", self.wrap_view('index'), name="index"),
        ]
        return pattern_list

    def specs(self, request, rid, repo_slug, state_slug=None, filename='specs.4.8.gz'):
        # noinspection PyUnusedLocal
        repo_slug = repo_slug
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.archive_type)
        if state_slug:
            filename = 'specs/%(slug)s/%(filename)s' % {'slug': state_slug, 'filename': filename, }
        else:
            filename = 'specs/%(filename)s' % {'filename': filename, }
        uid = self.storage_uid % repo.pk
        key = storage(settings.STORAGE_CACHE).uid_to_key(uid)
        return sendpath(settings.STORAGE_CACHE, key, filename, 'application/gzip')

    def quick_gem_specs(self, request, rid, repo_slug, state_slug=None, filename=None, compression=''):
        name, sep, version = filename.rpartition('-')
        if sep != '-':
            raise Http404
        # noinspection PyUnusedLocal
        repo_slug = repo_slug
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.archive_type)
        base_query = Element.objects.filter(repository=repo)
        if state_slug:
            state = get_object_or_404(ArchiveState, repository=repo, name=state_slug)
            base_query = base_query.filter(states=state)
        element = get_object_or_404(base_query, name=name, version=version)
        content = self.marshal_data(element)
        if compression == '.rz':
            content = zlib.compress(content)
        return HttpResponse(content, content_type='application/gzip')

    def gem_specs(self, request, rid, repo_slug, state_slug=None, filename=None):
        name, sep, version = filename.rpartition('-')
        if sep != '-':
            raise Http404
        # noinspection PyUnusedLocal
        repo_slug = repo_slug
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.archive_type)
        base_query = Element.objects.filter(repository=repo)
        if state_slug:
            state = get_object_or_404(ArchiveState, repository=repo, name=state_slug)
            base_query = base_query.filter(states=state)
        element = get_object_or_404(base_query, name=name, version=version)
        return HttpResponse(self.yaml_data(element), content_type='text/yaml')

    def download(self, request, rid, repo_slug, state_slug=None, filename=None):
        # noinspection PyUnusedLocal
        repo_slug = repo_slug
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.archive_type)
        base_query = Element.objects.filter(repository=repo)
        if state_slug:
            state = get_object_or_404(ArchiveState, repository=repo, name=state_slug)
            base_query = base_query.filter(states=state)
        element = get_object_or_404(base_query, filename=filename)
        from moneta.views import get_file
        return get_file(request, element.pk)

    def index(self, request, rid, repo_slug=None, state_slug=None):
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.archive_type)
        states = list(ArchiveState.objects.filter(repository=repo).order_by('name'))
        template_values = {'repo': repo, 'states': states, 'upload_allowed': repo.upload_allowed(request),
                           'admin_allowed': repo.admin_allowed(request), }
        view_name = moneta_url(repo, 'index')
        tab_infos = [
            (reverse(view_name, kwargs={'rid': repo.id, 'repo_slug': repo.slug}), states,
             ArchiveState(name=_('All states'), slug='all-states')),
        ]
        for state in states:
            tab_infos.append(
                (reverse(view_name, kwargs={'rid': repo.id, 'repo_slug': repo.slug, 'state_slug': state.slug}),
                 [state], state)
            )
        template_values['tab_infos'] = tab_infos
        return TemplateResponse(request, 'repositories/ruby/index.html', template_values)

    def generate_indexes(self, repo: Repository, states=None, validity=365):
        if states is None:
            states = list(ArchiveState.objects.filter(repository=repo))
        base_query = Element.objects.filter(repository=repo).prefetch_related('states')
        state_infos = [(None, None)] + [(state.slug, state.pk) for state in states]
        all_elements = {state_info[0]: [] for state_info in state_infos}
        all_specs = {state_info[0]: [] for state_info in state_infos}
        last_elements = {state_info[0]: {} for state_info in state_infos}
        for element in base_query:
            element_spec = self.python_data(element)
            assert isinstance(element_spec, Specification)
            element_data = [element.archive, element_spec.version, element_spec.platform]
            all_specs[None].append(element_spec)
            if 'date' in element_spec.values:
                del element_spec.values['date']
            all_elements[None].append(element_data)
            last_elements[None].setdefault(element_spec.name, []).append((element_spec.version.version,
                                                                          element_spec.platform))
            for state in element.states.all():
                all_elements[state.slug].append(element_data)
                all_specs[state.slug].append(element_spec)
                last_elements[state.slug].setdefault(element_spec.name, []).append((element_spec.version.version,
                                                                                    element_spec.platform))

        for state_info in state_infos:
            folder_name = 'specs/' if state_info[0] is None else 'specs/%(slug)s' % {'slug': state_info[0]}

            last_elements_by_state = []
            for name, versions in last_elements[state_info[0]].items():
                try:
                    versions.sort(key=lambda x: LooseVersion(x[0]))
                    last_elements_by_state.append([name, Version([versions[-1][0]]), versions[-1][1].encode('utf-8')])
                except ValueError:
                    continue
            names = list(last_elements[state_info[0]].keys())
            names.sort()

            def versions_write_fn(file_obj):
                for y in names:
                    version_txt = ('%s %s\n' % (y, ','.join([z[0] for z in last_elements[state_info[0]][y]])))
                    file_obj.write(version_txt.encode('utf-8'))

            def names_write_fn(file_obj):
                for y in names:
                    file_obj.write(('%s\n' % y).encode('utf-8'))

            self.__write_file(repo, '%s/specs.4.8' % folder_name, lambda x: write(x, all_elements))
            self.__write_file(repo, '%s/latest_specs.4.8' % folder_name, lambda x: write(x, last_elements_by_state))
            self.__write_file(repo, '%s/prerelease_specs.4.8' % folder_name, lambda x: write(x, []))
            self.__write_file(repo, '%s/Marshal.4.8' % folder_name, lambda x: write(x, all_specs))
            self.__write_file(repo, '%s/versions.list' % folder_name, versions_write_fn)
            self.__write_file(repo, '%s/names.list' % folder_name, names_write_fn)

    def __write_file(self, repo, dest_filename, write_function):
        uid = self.storage_uid % repo.pk
        key = storage(settings.STORAGE_CACHE).uid_to_key(uid)
        plain_file = tempfile.NamedTemporaryFile(mode='w+b', dir=settings.FILE_UPLOAD_TEMP_DIR, delete=False)
        gz_plain_file = tempfile.NamedTemporaryFile(mode='w+b', dir=settings.FILE_UPLOAD_TEMP_DIR, delete=False)
        gz_file = gzip.open(gz_plain_file, 'wb')
        write_function(plain_file)
        plain_file.flush()
        plain_file.seek(0)
        for block in iter(lambda: plain_file.read(8192), b''):
            gz_file.write(block)
        gz_file.close()
        gz_plain_file.close()
        storage(settings.STORAGE_CACHE).import_filename(plain_file.name, key, dest_filename)
        storage(settings.STORAGE_CACHE).import_filename(gz_plain_file.name, key, dest_filename + '.gz')
