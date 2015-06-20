import gzip
import hashlib
import os.path
import tarfile
import tempfile
# noinspection PyCompatibility
import bz2
from moneta.templatetags.moneta import moneta_url

try:
    import lzma
except ImportError:
    lzma = None
import datetime

from django.conf import settings
from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.http.response import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.timezone import get_current_timezone
from django.utils.translation import ugettext as _

from moneta.archives import ArFile
from moneta.exceptions import InvalidRepositoryException
from moneta.repository.signing import GPGSigner
from moneta.utils import parse_control_data
from moneta.views import get_file, sendpath
from moneta.repositories.base import RepositoryModel
from moneta.repository.models import storage, Repository, Element, ArchiveState


__author__ = 'flanker'

tz = get_current_timezone()


class Aptitude(RepositoryModel):
    verbose_name = _('APT repository for Linux .deb packages')
    storage_uid = 'a97172de-0000-0000-0000-%012d'
    archive_type = 'aptitude'
    index_html = 'repositories/aptitude/index.html'

    def is_file_valid(self, uploaded_file):
        return uploaded_file.name.endswith('.deb')

    def update_element(self, element):
        """
        Extract some informations from element to prepare the repository
        :param element: Element to add to the repository
        :return: Unicode string containing meta-data

        ar -x control.tar.gz
        tar -xf control.tar.gz control
        """
        archive_file = storage(settings.STORAGE_ARCHIVE).get_file(element.archive_key)
        ar_file = ArFile(element.filename, mode='r', fileobj=archive_file)
        control_file = self.get_subfile(ar_file, 'control.tar.')
        if control_file is None:
            raise InvalidRepositoryException('No control file found in .deb package')
        tar_file = tarfile.open(name='control', mode='r:*', fileobj=control_file)
        control_data = tar_file.extractfile('./control')
        # poulating different informations on the element
        control_data_value = control_data.read().decode('utf-8')
        control_data.close()
        tar_file.close()
        ar_file.close()
        archive_file.close()
        element.extra_data = control_data_value
        parsed_data = parse_control_data(control_data_value)
        element.archive = parsed_data['Package']
        element.version = parsed_data['Version']
        element.official_link = parsed_data.get('Homepage', '')
        element.long_description = parsed_data.get('Description', '')

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

    @staticmethod
    def get_subfile(ar_file, prefix='control.tar.'):
        for name in ar_file.getnames():
            if name.startswith(prefix):
                return ar_file.extractfile(name)
        return None

    def file_list(self, element, uid):
        cache_filename = 'filelist_%s' % element.sha256
        key = storage(settings.STORAGE_CACHE).uid_to_key(uid)
        fileobj = storage(settings.STORAGE_CACHE).get_file(key, cache_filename)
        if fileobj is None:
            tmpfile = tempfile.NamedTemporaryFile(dir=settings.TEMP_ROOT)
            archive_file = storage(settings.STORAGE_ARCHIVE).get_file(element.archive_key, sub_path='')
            ar_file = ArFile(element.filename, mode='r', fileobj=archive_file)
            data_file = self.get_subfile(ar_file, 'data.tar.')
            tar_file = tarfile.open(name='data', mode='r:*', fileobj=data_file)
            members = tar_file.getmembers()
            members = filter(lambda x: x.isfile(), members)
            names = [x.path[2:] for x in members]
            tar_file.close()
            ar_file.close()
            archive_file.close()
            for name in names:
                tmpfile.write(('%s\n' % name).encode('utf-8'))
            tmpfile.flush()
            tmpfile.seek(0)
            storage(settings.STORAGE_CACHE).store_descriptor(uid, cache_filename, tmpfile)
            tmpfile.close()
        else:
            names = [line.strip().decode() for line in fileobj]
            fileobj.close()
        return names

    def url_list(self):
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
            url(r'^(?P<rid>\d+)/force_index/(?P<repo_slug>[\w\-\._]+)/$', self.wrap_view('force_index'), name='force_index'),
        ]
        return pattern_list

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
        compression = '(?P<compression>|.bz2|.gz|.xz)'
        if lzma is None:
            compression = '(?P<compression>|.bz2|.gz)'
        pattern_list = [
            url(r"^(?P<rid>\d+)/pool/(?P<repo_slug>[\w\-\._]+)/(?P<state_slug>[\w\-\._]+)/(?P<folder>[\w\-\.]+)/$",
                self.wrap_view('folder_index'), name="folder_index"),
            url(r"^(?P<rid>\d+)/pool/(?P<repo_slug>[\w\-\._]+)/(?P<state_slug>[\w\-\._]+)/(?P<folder>[\w\-\.]+)/"
                r"(?P<filename>[\w\-\.]+)$",
                self.wrap_view('get_file'), name="get_file"),
            url(r"^(?P<rid>\d+)/dists/(?P<repo_slug>[\w\-\._]+)/(?P<filename>Release|Release.gpg)$",
                self.wrap_view('repo_release'), name="repo_release"),
            url(r"^(?P<rid>\d+)/dists/(?P<repo_slug>[\w\-\._]+)/Contents-(?P<arch>[\w]+)"
                r"%s$" % compression, self.wrap_view('arch_contents'), name="arch_contents"),
            url(r"^(?P<rid>\d+)/dists/(?P<repo_slug>[\w\-\._]+)/(?P<state_slug>[\w\-\._]+)/"
                r"Contents-(?P<arch>[\w\-\.]+)%s$" % compression,
                self.wrap_view('state_contents'), name="state_contents"),
            url(r"^(?P<rid>\d+)/dists/(?P<repo_slug>[\w\-\._]+)/(?P<state_slug>[\w\-\._]+)/binary-(?P<arch>[\w\-\.]+)/"
                r"(?P<filename>Packages|Release)%s$" % compression,
                self.wrap_view('state_files'), name="state_files"),
            url(r"^(?P<rid>\d+)/(?P<slug2>[\w\-\._]+)/(?P<repo_slug>[\w\-\._]+).asc$", self.wrap_view('gpg_key'),
                name="gpg_key"),
            url(r"^(?P<rid>\d+)/$", self.wrap_view('index'), name="index"),
        ]
        return pattern_list

    def extra_index_urls(self, request, repo):
        """ Provides an iterable of tuples (URL, name), to add on the main index
        """
        result = []
        force_index = (reverse('%s:force_index' % self.archive_type, kwargs={'rid': repo.id, 'repo_slug': repo.slug}),
                       _('Index packages'))
        result.append(force_index)
        return result

    # noinspection PyUnusedLocal,PyMethodMayBeStatic
    def gpg_key(self, request, rid, repo_slug, slug2):
        get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.archive_type)
        signature = GPGSigner().export_key()
        return HttpResponse(signature, content_type="text/plain")

    def repo_release(self, request, rid, repo_slug, filename):
        filename = 'dists/%(repo)s/%(filename)s' % {'repo': repo_slug, 'filename': filename}
        return self.index_file(request, rid, filename, 'text/plain')

    def state_files(self, request, rid, repo_slug, state_slug, arch, filename, compression):
        filename = 'dists/%(repo)s/%(state)s/binary-%(arch)s/%(filename)s%(comp)s' % {
            'repo': repo_slug, 'state': state_slug, 'arch': arch, 'filename': filename, 'comp': compression}
        return self.index_file(request, rid, filename, 'text/plain')

    def arch_contents(self, request, rid, repo_slug, arch, compression):
        filename = 'dists/%(repo)s/Contents-%(arch)s%(comp)s' % {'repo': repo_slug, 'arch': arch, 'comp': compression, }
        return self.index_file(request, rid, filename, 'text/plain')

    def state_contents(self, request, rid, repo_slug, state_slug, arch, compression):
        filename = 'dists/%(repo)s/%(state)s/Contents-%(arch)s%(comp)s' % \
                   {'repo': repo_slug, 'arch': arch, 'comp': compression, 'state': state_slug, }
        return self.index_file(request, rid, filename, 'text/plain')

    def index_file(self, request, rid, filename, mimetype):
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.archive_type)
        uid = self.storage_uid % repo.id
        key = storage(settings.STORAGE_CACHE).uid_to_key(uid)
        return sendpath(settings.STORAGE_CACHE, key, filename, mimetype)

    # noinspection PyUnusedLocal
    def folder_index(self, request, rid, repo_slug, state_slug, folder):
        """
        Return a HttpResponse
        :param request: HttpRequest
        :raise:
        """
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.archive_type)
        state = get_object_or_404(ArchiveState, repository=repo, slug=state_slug)
        q = Element.objects.filter(repository__id=rid, archive__startswith=folder, states=state)
        element_query = q.select_related()[0:100]
        element_count = q.count()
        template_values = {'repo': repo, 'state': state_slug, 'element_count': element_count,
                           'elements': element_query, 'folder': folder,
                           'upload_allowed': repo.upload_allowed(request), }
        return render_to_response('repositories/aptitude/folder_index.html', template_values,
                                  RequestContext(request))

    # noinspection PyUnusedLocal
    def get_file(self, request, rid, repo_slug, state_slug, folder, filename):
        """
        Return a HttpResponse
        :param request: HttpRequest
        :raise:
        """
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.archive_type)
        q = Element.objects.filter(repository__id=rid, filename=filename)[0:1]
        q = list(q)
        if len(q) == 0:
            raise Http404
        element = q[0]
        return get_file(request, element.id, compression=None, path='', element=element, name=None)

    def index(self, request, rid):
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.archive_type)
        states = [state for state in ArchiveState.objects.filter(repository=repo).order_by('name')]
        tab_infos = [(states, ArchiveState(name=_('All states'), slug='all-states')), ]
        tab_infos += [([state], state) for state in states]

        template_values = {'repo': repo, 'states': states, 'upload_allowed': repo.upload_allowed(request),
                           'index_url': reverse(moneta_url(repo, 'index'), kwargs={'rid': repo.id, }),
                           'tab_infos': tab_infos, 'admin_allowed': repo.admin_allowed(request), }
        return render_to_response(self.index_html, template_values, RequestContext(request))

    # noinspection PyUnusedLocal
    def force_index(self, request, rid, repo_slug):
        repo = get_object_or_404(Repository.upload_queryset(request), id=rid, archive_type=self.archive_type)
        self.generate_indexes(repo)
        return HttpResponse(_('Indexes have been successfully rebuilt.'))

    @staticmethod
    def compress_files(open_files: dict, root: str, uid: str) -> list:
        """ Return a list of tuples ((os.path.relpath(filename, root), md5, sha1, sha256, actual_size).
        Also stores the generated files (and original ones)

        :param open_files: dict[filename] = open file descriptor in mode w+b
        :param root:
        :param uid:
        :return:
        """
        hash_controls = []
        for filename, package_file in open_files.items():
            package_file.seek(0)
            gz_filename = filename + '.gz'
            bz2_filename = filename + '.bz2'
            xz_filename = filename + '.xz'
            gz_file = tempfile.TemporaryFile(mode='w+b', dir=settings.TEMP_ROOT)
            bz2_file = tempfile.TemporaryFile(mode='w+b', dir=settings.TEMP_ROOT)
            xz_file = tempfile.TemporaryFile(mode='w+b', dir=settings.TEMP_ROOT)
            bz2_compressor = bz2.BZ2Compressor(9)
            if lzma is not None:
                xz_compressor = lzma.LZMACompressor()
            else:
                xz_compressor = bz2_compressor
            with gzip.GzipFile(gz_filename, mode='wb', compresslevel=9, fileobj=gz_file) as fd_gz:
                data = package_file.read(10240)
                while data:
                    fd_gz.write(data)
                    bz2_file.write(bz2_compressor.compress(data))
                    xz_file.write(xz_compressor.compress(data))
                    data = package_file.read(10240)
            bz2_file.write(bz2_compressor.flush())
            xz_file.write(xz_compressor.flush())
            all_files = [(package_file, filename), (gz_file, gz_filename), (bz2_file, bz2_filename), ]
            if lzma is not None:
                all_files.append((xz_file, xz_filename))
            for obj, filename in all_files:
                obj.flush()
                obj.seek(0)
                data = obj.read(32768)
                md5, sha1, sha256, size = hashlib.md5(), hashlib.sha1(), hashlib.sha256(), 0
                while data:
                    md5.update(data)
                    sha1.update(data)
                    sha256.update(data)
                    size += len(data)
                    data = obj.read(32768)
                hash_controls.append((os.path.relpath(filename, root), md5.hexdigest(), sha1.hexdigest(),
                                      sha256.hexdigest(), size))
                obj.seek(0)
                storage(settings.STORAGE_CACHE).store_descriptor(uid, filename, obj)
                obj.close()
                # build the following files:
        return hash_controls

    def generate_indexes(self, repository, states=None, validity=365):
        default_architectures = {'amd64', }
        uid = self.storage_uid % repository.id
        repo_slug = repository.slug
        root_url = reverse('%s:index' % self.archive_type, kwargs={'rid': repository.id, })
        if repository.is_private:
            root_url = 'authb-%s' % root_url
        if states is None:
            states = list(ArchiveState.objects.filter(repository=repository).order_by('name'))
        states = [state for state in states if
                  Element.objects.filter(repository=repository, states=state).count() > 0]

        all_states_architectures = set()
        all_states = set()
        open_files = {}
        complete_file_list = {}
        root = 'dists/%(repo)s/' % {'repo': repo_slug}
        # list all available architectures (required to add architecture-independent packages to all archs)
        for element in Element.objects.filter(repository=repository):
            control_data = parse_control_data(element.extra_data)
            architecture = control_data.get('Architecture', 'all')
            all_states_architectures.add(architecture)
            # build the following files:
        #   * dists/(group)/(state)/binary-(architecture)/Packages
        #   * dists/(group)/(state)/binary-(architecture)/Release
        # prepare data for:
        #   * dists/(group)/Contents-(architecture)
        if not all_states_architectures or all_states_architectures == {'all'}:
            all_states_architectures = default_architectures
        for state in states:
            state_architectures = set()
            all_states.add(state.name)
            for element in Element.objects.filter(repository=repository, states=state).order_by('filename'):
                control_data = parse_control_data(element.extra_data)
                architecture = control_data.get('Architecture', 'all')
                section = control_data.get('Section', 'contrib')
                package_file_list = ["%- 100s%s\n" % (x, section) for x in self.file_list(element, uid)]
                if architecture == 'all':
                    elt_architectures = default_architectures
                else:
                    elt_architectures = {architecture, }
                state_architectures |= elt_architectures
                for architecture in elt_architectures:
                    complete_file_list.setdefault(architecture, [])
                    complete_file_list[architecture] += package_file_list

                    filename = 'dists/%(repo)s/%(state)s/binary-%(architecture)s/Packages' % {
                        'repo': repo_slug, 'state': state.name, 'architecture': architecture, }
                    if filename not in open_files:
                        open_files[filename] = tempfile.TemporaryFile(mode='w+b', dir=settings.TEMP_ROOT)
                    package_file = open_files[filename]
                    package_file.write(element.extra_data.encode('utf-8'))
                    for key, attr in (('MD5sum', 'md5'), ('SHA1', 'sha1'), ('SHA256', 'sha256'),
                                      ('Size', 'filesize')):
                        if key not in control_data:
                            package_file.write("{0}: {1}\n".format(key, getattr(element, attr)).encode('utf-8'))
                    package_url = reverse('%s:get_file' % self.archive_type,
                                          kwargs={'rid': repository.id, 'repo_slug': repo_slug,
                                                  'filename': element.filename, 'state_slug': state.slug,
                                                  'folder': element.filename[0:1], })
                    package_url = os.path.relpath(package_url, root_url)
                    package_file.write("Filename: {0}\n".format(package_url).encode('utf-8'))
                    package_file.write("\n".encode('utf-8'))
            if len(state_architectures) == 0:
                state_architectures = default_architectures
                # we process elements
            for architecture in state_architectures:
                filename = 'dists/%(repo)s/%(state)s/binary-%(architecture)s/Release' % {
                    'repo': repo_slug, 'state': state.slug, 'architecture': architecture,
                }
                open_files[filename] = tempfile.TemporaryFile(mode='w+b', dir=settings.TEMP_ROOT)
                content = render_to_string('repositories/aptitude/architecture_release.txt',
                                           {'architecture': architecture, 'repository': repository, 'state': state, })
                open_files[filename].write(content.encode('utf-8'))
            # build the following files:
        #   * dists/(group)/Contents-(architecture)
        for architecture, file_list in complete_file_list.items():
            file_list.sort()
            filename = 'dists/%(repo)s/Contents-%(architecture)s' % {'repo': repo_slug,
                                                                     'architecture': architecture, }
            open_files[filename] = tempfile.TemporaryFile(mode='w+b', dir=settings.TEMP_ROOT)
            open_files[filename].write(render_to_string('repositories/aptitude/contents.txt').encode('utf-8'))
            for info in file_list:
                open_files[filename].write(info.encode('utf-8'))
            # build the following files:
        #   * dists/(group)/Contents-(architecture).gz/.bz2/.xz
        #   * dists/(group)/(state)/binary-(architecture)/Packages.gz/.bz2/.xz
        #   * dists/(group)/(state)/binary-(architecture)/Release.gz/.bz2/.xz
        # store all files in the cache
        hash_controls = self.compress_files(open_files, root, uid)
        #   * dists/(group)/Release
        # store all files in the cache
        release_file = tempfile.TemporaryFile(mode='w+b', dir=settings.TEMP_ROOT)
        now = datetime.datetime.now(tz)
        now_str = now.strftime('%a, %d %b %Y %H:%M:%S %z')  # 'Mon, 29 Nov 2010 08:12:51 UTC'
        until = (now + datetime.timedelta(validity)).strftime('%a, %d %b %Y %H:%M:%S %z')
        content = render_to_string('repositories/aptitude/state_release.txt',
                                   {'architectures': all_states_architectures, 'until': until,
                                    'states': all_states, 'repository': repository, 'date': now_str})
        release_file.write(content.encode('utf-8'))
        for hash_value, index in (('MD5Sum', 1), ('SHA1', 2), ('SHA256', 3)):
            release_file.write("{0}:\n".format(hash_value).encode('utf-8'))
            for line in hash_controls:
                release_file.write((" %s % 8d %s\n" % (line[index], line[4], line[0])).encode('utf-8'))
        release_file.flush()
        release_file.seek(0)
        filename = 'dists/%(repo)s/Release' % {'repo': repo_slug, }
        storage(settings.STORAGE_CACHE).store_descriptor(uid, filename, release_file)
        # build the following files:
        #   * dists/(group)/Release.gpg
        # store all files in the cache
        release_file.seek(0)
        signature = GPGSigner().sign_file(release_file)
        release_file.close()

        gpg_file = tempfile.TemporaryFile(mode='w+b', dir=settings.TEMP_ROOT)
        gpg_file.write(signature.encode('utf-8'))
        gpg_file.flush()
        gpg_file.seek(0)
        filename = 'dists/%(repo)s/Release.gpg' % {'repo': repo_slug, }
        storage(settings.STORAGE_CACHE).store_descriptor(uid, filename, gpg_file)
        gpg_file.close()
