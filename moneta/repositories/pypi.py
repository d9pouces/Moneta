from distutils.version import LooseVersion
import os.path
import tarfile
import zipfile

from django.conf import settings
from django.conf.urls import url
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import UploadedFile
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.timezone import get_current_timezone
from django.utils.translation import ugettext as _

from moneta.exceptions import InvalidRepositoryException
from moneta.templatetags.moneta import moneta_url
from moneta.utils import parse_control_data
from moneta.repositories.aptitude import Aptitude
from moneta.repositories.xmlrpc import XMLRPCSite, register_rpc_method
from moneta.repository.models import storage, Repository, Element, ArchiveState

__author__ = 'flanker'

tz = get_current_timezone()
XML_RPC_SITE = XMLRPCSite()


class PyArchive:
    def __init__(self, compressed_file, compression, prefix):
        self.compression = compression
        self.compressed_file = compressed_file
        self.prefix = prefix

    def get_pkg_info(self):
        # noinspection PyBroadException
        try:
            if self.compression == 'egg':
                control_data_file = self.compressed_file.open(os.path.join(self.prefix, 'EGG-INFO', 'PKG-INFO'))
            elif self.compression == 'tar':
                control_data_file = self.compressed_file.extractfile(os.path.join(self.prefix, 'PKG-INFO'))
                # poulating different informations on the element
            elif self.compression == 'whl':
                control_data_file = None
                for name in self.compressed_file.namelist():
                    components = name.split(os.path.sep)
                    if components[0].endswith('.dist-info') and components[1:] == ['METADATA']:
                        control_data_file = self.compressed_file.open(name)
                if control_data_file is None:
                    return None
            else:  # zip
                control_data_file = self.compressed_file.open(os.path.join(self.prefix, 'PKG-INFO'))
            control_data_value = control_data_file.read().decode('utf-8')
            control_data_file.close()
        except:
            return None
        return control_data_value

    def close(self):
        self.compressed_file.close()


class Pypi(Aptitude):
    verbose_name = _('Pypi repository for Python packages')
    storage_uid = '61610000-0000-0000-0000-%012d'
    archive_type = 'pypy'

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
            url(r"^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]*)/rpc/?$",
                self.wrap_view('xmlrpc', csrf_exempt=True), name="xmlrpc"),
            url(r"^\d+/[\w\-\._]+/[\w\-\._]+/f/(?P<eid>\d+)/.*$", self.wrap_view('get_filename'), name="get_file"),
            url(r"^(?P<rid>\d+)/$", self.wrap_view('index'), name="index"),
        ]
        return pattern_list

    def index(self, request, rid):
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.archive_type)
        states = list(ArchiveState.objects.filter(repository=repo).order_by('name'))
        template_values = {'repo': repo, 'states': states, 'upload_allowed': repo.upload_allowed(request),
                           'admin_allowed': repo.admin_allowed(request), }
        view_name = moneta_url(repo, 'simple')
        tab_infos = [
            (reverse(view_name, kwargs={'rid': repo.id, 'repo_slug': repo.slug}), states, ArchiveState(name=_('All states'), slug='all-states')),
        ]
        for state in states:
            tab_infos.append(
                (reverse(view_name, kwargs={'rid': repo.id, 'repo_slug': repo.slug, 'state_slug': state.slug}), [state], state)
            )
        template_values['tab_infos'] = tab_infos
        return render_to_response('repositories/pypi/index.html', template_values, RequestContext(request))

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

    def xmlrpc(self, request, rid, repo_slug, state_slug):
        return XML_RPC_SITE.dispatch(request, self, rid, repo_slug, state_slug)

    # noinspection PyMethodParameters,PyUnusedLocal
    @register_rpc_method(XML_RPC_SITE, name='search')
    def xr_search(request, rpc_args, self, rid, repo_slug, state_slug=None):
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.model)
        state = get_object_or_404(ArchiveState, repository=repo, name=state_slug) if state_slug else None
        global_and = len(rpc_args) == 0 or rpc_args[1] != 'or'
        if len(rpc_args) == 0 or not isinstance(rpc_args[0], dict):
            raise PermissionDenied
        filters = None
        for query_name, attr_name in (('name', 'archive'), ('version', 'version'), ('home_page', 'official_link'),
                                      ('description', 'long_description'),):
            if query_name in rpc_args[0]:
                value = rpc_args[0][query_name]
                if isinstance(value, list):
                    if value:
                        value = value[0]
                    else:
                        value = ''
                value = value.replace('-', '').replace('_', '')
                sub_query = Q(**{attr_name + '__icontains': value})
                if filters is None:
                    filters = sub_query
                elif global_and:
                    filters = filters and sub_query
                else:
                    filters = filters or sub_query
        query = Element.objects.filter(repository=repo)
        if state:
            query = query.filter(states=state)
        if filters is not None:
            query = query.filter(filters)
        res = [{'name': x.archive, 'version': x.version, 'summary': x.long_description,
                '_pypi_ordering': 1.0} for x in query]
        return res

    # noinspection PyMethodParameters,PyUnusedLocal
    @register_rpc_method(XML_RPC_SITE, name='list_packages')
    def xr_list_packages(request, rpc_args, self, rid, repo_slug, state_slug=None):
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.model)
        if state_slug:
            state = get_object_or_404(ArchiveState, repository=repo, name=state_slug)
            query = Element.objects.filter(repository=repo, states=state).order_by('name')
        else:
            query = Element.objects.filter(repository=repo).order_by('name')
        results = []
        prev = None
        for value in query:
            if value.name != prev:
                results.append(value.name)
                prev = value.name
        return results

    # noinspection PyMethodParameters,PyUnusedLocal
    @register_rpc_method(XML_RPC_SITE, name='package_releases')
    def xr_package_releases(request, rpc_args, self, rid, repo_slug, state_slug=None):
        if len(rpc_args) == 0:
            raise PermissionDenied
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.model)
        if state_slug:
            state = get_object_or_404(ArchiveState, repository=repo, name=state_slug)
            query = Element.objects.filter(repository=repo, states=state, archive=rpc_args[0])
        else:
            query = Element.objects.filter(repository=repo, archive=rpc_args[0])
        versions = [LooseVersion(x.version) for x in query]
        versions.sort()
        return [str(x) for x in versions]

    # noinspection PyMethodParameters,PyUnusedLocal
    @register_rpc_method(XML_RPC_SITE, name='user_packages')
    def xr_user_packages(request, rpc_args, self, rid, repo_slug, state_slug=None):
        if len(rpc_args) == 0:
            raise PermissionDenied
        author = str(rpc_args[0]).lower()
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.model)
        if state_slug:
            state = get_object_or_404(ArchiveState, repository=repo, name=state_slug)
            query = Element.objects.filter(repository=repo, state=state).filter(author__name__icontains=author) \
                .order_by('name')
        else:
            query = Element.objects.filter(repository=repo).filter(author__name__icontains=author).order_by('name')
        results = []
        prev = None
        for value in query:
            if value.name != prev:
                results.append(('Owner', value.name))
                prev = value.name
        return results

    # noinspection PyMethodParameters,PyUnusedLocal
    @register_rpc_method(XML_RPC_SITE, name='release_urls')
    def xr_release_urls(request, rpc_args, self, rid, repo_slug, state_slug=None):
        if len(rpc_args) != 2:
            raise PermissionDenied
        name = rpc_args[0]
        version = rpc_args[1]
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.model)
        if state_slug:
            state = get_object_or_404(ArchiveState, repository=repo, name=state_slug)
            query = Element.objects.filter(repository=repo, state=state).filter(archive=name, version=version)
        else:
            query = Element.objects.filter(repository=repo).filter(archive=name, version=version)
        results = []
        # noinspection PyUnresolvedReferences
        base = request.build_absolute_uri('/')[:-1]
        for element in query:
            view_name = moneta_url(repo, 'get_file')
            package_url = base + reverse(view_name, kwargs={'eid': element.id, })
            results.append({'url': package_url, 'packagetype': 'sdist',
                            'filename': element.filename, 'size': element.filesize, 'downloads': 0,
                            'comment_text': element.long_description, 'md5_dist': element.md5, 'has_sig': False,
                            'python_version': 'source', })
        return results

    # noinspection PyMethodParameters,PyUnusedLocal
    @register_rpc_method(XML_RPC_SITE, name='release_data')
    def xr_release_data(request, rpc_args, self, rid, repo_slug, state_slug=None):
        if len(rpc_args) != 2:
            raise PermissionDenied
        name = rpc_args[0]
        version = rpc_args[1]
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.model)
        if state_slug:
            stat = get_object_or_404(ArchiveState, repository=repo, name=state_slug)
            query = list(Element.objects.filter(repository=repo, state=stat).filter(archive=name, version=version)[0:1])
        else:
            query = list(Element.objects.filter(repository=repo).filter(archive=name, version=version)[0:1])
        if not query:
            return {}
        element = query[0]
        result = {}
        for query_name, attr_name in (('name', 'archive'), ('version', 'version'), ('home_page', 'official_link'),
                                      ('description', 'long_description'), ('author', 'author')):
            result[query_name] = str(getattr(element, attr_name))
        for k in ('author_email', 'maintainer', 'maintainer_email', 'license', 'summary', 'keywords', 'platform',
                  'download_url'):
            result[k] = ''
        return result

    # noinspection PyMethodParameters,PyUnusedLocal,PyMethodMayBeStatic
    @register_rpc_method(XML_RPC_SITE, name='package_roles')
    def xr_package_roles(request, rpc_args, self, rid, repo_slug, state_slug=None):
        return []
