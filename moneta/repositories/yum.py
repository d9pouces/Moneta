# -*- coding: utf-8 -*-
import os
import tempfile
import datetime

from django.conf import settings
from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from pyrpm import rpm
from pyrpm.rpm import RPM, HeaderBase, RPMError

from django.utils.translation import ugettext as _

from moneta.repositories.aptitude import Aptitude, tz
from moneta.repository.models import Repository, storage, Element, ArchiveState
from moneta.repository.signing import GPGSigner
from moneta.utils import parse_control_data
from moneta.views import sendpath

__author__ = 'flanker'

RPMTAG_NAME = 1000
RPMTAG_VERSION = 1001
RPMTAG_RELEASE = 1002
RPMTAG_SERIAL = 1003
RPMTAG_SUMMARY = 1004
RPMTAG_DESCRIPTION = 1005
RPMTAG_BUILDTIME = 1006
RPMTAG_BUILDHOST = 1007
RPMTAG_INSTALLTIME = 1008
RPMTAG_SIZE = 1009
RPMTAG_DISTRIBUTION = 1010
RPMTAG_VENDOR = 1011
RPMTAG_GIF = 1012
RPMTAG_XPM = 1013
RPMTAG_COPYRIGHT = 1014
RPMTAG_PACKAGER = 1015
RPMTAG_GROUP = 1016
RPMTAG_CHANGELOG = 1017
RPMTAG_SOURCE = 1018
RPMTAG_PATCH = 1019
RPMTAG_URL = 1020
RPMTAG_OS = 1021
RPMTAG_ARCH = 1022
RPMTAG_PREIN = 1023
RPMTAG_POSTIN = 1024
RPMTAG_PREUN = 1025
RPMTAG_POSTUN = 1026
RPMTAG_FILENAMES = 1027
RPMTAG_FILESIZES = 1028
RPMTAG_FILESTATES = 1029
RPMTAG_FILEMODES = 1030
RPMTAG_FILEUIDS = 1031
RPMTAG_FILEGIDS = 1032
RPMTAG_FILERDEVS = 1033
RPMTAG_FILEMTIMES = 1034
RPMTAG_FILEMD5S = 1035
RPMTAG_FILELINKTOS = 1036
RPMTAG_FILEFLAGS = 1037
RPMTAG_ROOT = 1038
RPMTAG_FILEUSERNAME = 1039
RPMTAG_FILEGROUPNAME = 1040
RPMTAG_EXCLUDE = 1041
RPMTAG_EXCLUSIVE = 1042
RPMTAG_ICON = 1043
RPMTAG_SOURCERPM = 1044
RPMTAG_FILEVERIFYFLAGS = 1045
RPMTAG_ARCHIVESIZE = 1046
RPMTAG_PROVIDES = 1047
RPMTAG_REQUIREFLAGS = 1048
RPMTAG_REQUIRENAME = 1049
RPMTAG_REQUIREVERSION = 1050
RPMTAG_NOSOURCE = 1051
RPMTAG_NOPATCH = 1052
RPMTAG_CONFLICTFLAGS = 1053
RPMTAG_CONFLICTNAME = 1054
RPMTAG_CONFLICTVERSION = 1055
RPMTAG_DEFAULTPREFIX = 1056
RPMTAG_BUILDROOT = 1057
RPMTAG_INSTALLPREFIX = 1058
RPMTAG_EXCLUDEARCH = 1059
RPMTAG_EXCLUDEOS = 1060
RPMTAG_EXCLUSIVEARCH = 1061
RPMTAG_EXCLUSIVEOS = 1062
RPMTAG_AUTOREQPROV = 1063
RPMTAG_RPMVERSION = 1064
RPMTAG_TRIGGERSCRIPTS = 1065
RPMTAG_TRIGGERNAME = 1066
RPMTAG_TRIGGERVERSION = 1067
RPMTAG_TRIGGERFLAGS = 1068
RPMTAG_TRIGGERINDEX = 1069
RPMTAG_VERIFYSCRIPT = 1079


class MyHeaderBase(object):
    """ optimized version of HeaderBase, avoiding O(n)-lookup at each attribute access.
    """
    _header_attr = ''

    def __init__(self, rpm_obj: RPM):
        self._values = {}
        available_values = {}
        header = getattr(rpm_obj, self._header_attr)
        assert isinstance(header, HeaderBase)
        for entry in header:
            available_values[entry.tag] = entry.value
        for attr_name, infos in header.TAGS.items():
            self._values[attr_name] = available_values.get(infos[0], infos[1])

    def __getattr__(self, name: str):
        if name in self._values:
            return self._values[name]
        raise AttributeError(name)


class Signature(MyHeaderBase):
    _header_attr = 'signature'


class Header(MyHeaderBase):
    _header_attr = 'header'


class Yum(Aptitude):
    verbose_name = _('YUM repository for Linux .rpm packages')
    storage_uid = 'a87172de-0000-0000-0000-%012d'
    archive_type = 'aptitude'

    def is_file_valid(self, uploaded_file):
        if not uploaded_file.name.endswith('.rpm'):
            return False
        try:
            rpm.RPM(uploaded_file.file)
        except RPMError:
            return False
        return True

    def update_element(self, element):
        fd = storage(settings.STORAGE_ARCHIVE).get_file(element.archive_key)
        rpm_obj = rpm.RPM(fd)
        element.filename = rpm_obj.canonical_filename
        element.version = rpm_obj.header.version
        element.archive = rpm_obj.header.name

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
        compression = '(?P<compression>|.bz2|.gz)'
        pattern_list = [
            url(r'^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]+)/(?P<state_slug>[\w\-\._]+)/Packages/$',
                self.wrap_view('folder_index'), name='folder_index'),
            url(r'^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]+)/(?P<state_slug>[\w\-\._]+)/Packages/'
                r'(?P<filename>[\w\-\.]+)$', self.wrap_view('get_file'), name='get_file'),
            url(r'^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]+)/(?P<state_slug>[\w\-\._]+)/(?P<arch>[\w\-\._]+)/repodata/'
                r'(?P<filename>[\w\-\.]+)%s$' % compression, self.wrap_view('repodata_file'), name='repodata_file'),
            url(r"^(?P<rid>\d+)/(?P<slug>[\w\-\._]+)/(?P<repo_slug>[\w\-\._]+).asc$", self.wrap_view('gpg_key'),
                name="gpg_key"),
            url(r"^(?P<rid>\d+)/$", self.wrap_view('index'), name="index"),
        ]
        return pattern_list

    # noinspection PyUnusedLocal,PyMethodMayBeStatic
    def gpg_key(self, request, rid, repo_slug, slug2):
        get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.archive_type)
        signature = GPGSigner().export_key()
        return HttpResponse(signature, content_type="text/plain")

    def repodata_file(self, request, rid, repo_slug, state_slug, filename, compression):
        if filename not in ('comps.xml', 'primary.xml', 'other.xml', 'filelists.xml',
                            'comps.sqlite', 'primary.sqlite', 'other.sqlite', 'filelists.sqlite',):
            return HttpResponse(_('File not found'), status=404)
        mimetype = ''
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.archive_type)
        uid = self.storage_uid % repo.id
        key = storage(settings.STORAGE_CACHE).uid_to_key(uid)
        return sendpath(settings.STORAGE_CACHE, key, filename + compression, mimetype)

    @staticmethod
    def get_package_template_values(rpm_obj: rpm.RPM) -> dict:
        return {'rpm': rpm_obj, 'header': Header(rpm_obj), 'signature': Signature(rpm_obj), }

    def generate_indexes(self, repository, states=None, validity=365):
        # files to generate:

        # primary.xml -> list of packages
        #   <?xml version="1.0" encoding="UTF-8"?>
        #   <metadata xmlns="http://linux.duke.edu/metadata/common" xmlns:rpm="http://linux.duke.edu/metadata/rpm" packages="8652">
        #   <package type="rpm">
        #   </package>
        #   </metadata>

        # comps.xml
        #   <?xml version="1.0" encoding="UTF-8"?>
        #   <!DOCTYPE comps PUBLIC "-//CentOS//DTD Comps info//EN" "comps.dtd">
        #   <comps>
        #   </comps>

        # filelists.xml
        #   <?xml version="1.0" encoding="UTF-8"?>
        #   <filelists xmlns="http://linux.duke.edu/metadata/filelists" packages="8652">
        #   <package pkgid="e8ed9e0612e813491ed5e7c10502a39e43ec665afd1321541dea211202707a65" name="389-ds-base" arch="x86_64">
        #     <version epoch="0" ver="1.3.3.1" rel="13.el7"/>
        #     <file>/etc/dirsrv/config/certmap.conf</file>
        #   </package>
        #   </filelists>

        # other.xml
        #   <?xml version="1.0" encoding="UTF-8"?>
        #   <otherdata xmlns="http://linux.duke.edu/metadata/other" packages="8652">
        #   <package pkgid="e8ed9e0612e813491ed5e7c10502a39e43ec665afd1321541dea211202707a65" name="389-ds-base" arch="x86_64">
        #     <version epoch="0" ver="1.3.3.1" rel="13.el7"/>
        #     <changelog author="Noriko Hosoi &lt;nhosoi@redhat.com&gt; - 1.3.3.1-4" date="1412164800">- release 1.3.3.1-4
        #   </package>
        #   </otherdata>
        if states is None:
            states = list(ArchiveState.objects.filter(repository=repository).order_by('name'))

        architectures_by_state = {x.slug: set() for x in states}  # architectures_by_state[archive_state.slug] = {'x86_64', 'c7', }
        # open all RPM objects
        rpm_objects = []
        package_count_by_state_arch = {x.slug: {} for x in states}
        for element in Element.objects.filter(repository=repository).select_related('states'):
            storage_obj = storage(settings.STORAGE_ARCHIVE)
            fd = storage_obj.get_file(element.archive_key, sub_path='')
            rpm_obj = rpm.RPM(fd)
            rpm_objects.append(rpm_obj)
            fd.close()
            rpm_obj.states = [s.slug for s in element.states.all()]
            package_architecture = 'noarch'
            for entry in rpm_obj.header.entries:
                if entry.tag == RPMTAG_ARCH:
                    package_architecture = entry.value
            if package_architecture != 'noarch':
                for state_slug in rpm_obj.states:
                    architectures_by_state[state_slug].add(package_architecture)
            for state_slug in rpm_obj.states:
                package_count_by_state_arch[state_slug].setdefault(package_architecture, 0)
                package_count_by_state_arch[state_slug][package_architecture] += 1

        # add the count of 'noarch' packages to other architectures
        for state_slug, package_count_by_arch in package_count_by_state_arch.items():
            t = package_count_by_arch.setdefault('noarch', 0)
            if len(package_count_by_arch) == 1:  # only 'noarch' architecture
                package_count_by_arch['x86_64'] = 0
                architectures_by_state[state_slug] = {'x86_64'}
            for architecture in package_count_by_arch:
                package_count_by_arch[architecture] += t
            del package_count_by_arch['noarch']

        # prepare all files
        open_files = {}
        for state_slug, architectures in architectures_by_state.items():
            for architecture in architectures:
                for name in ('other.xml', 'filelists.xml', 'comps.xml', 'primary.xml'):
                    filename = self.index_filename(state_slug, architecture, name)
                    open_files[filename] = tempfile.TemporaryFile(mode='w+')
                    open_files[filename].write('<?xml version="1.0" encoding="UTF-8"?>\n')
                package_count = package_count_by_state_arch[state_slug][architecture]

                header = '<otherdata xmlns="http://linux.duke.edu/metadata/other" packages="%d">\n' % package_count
                open_files[self.index_filename(state_slug, architecture, 'other.xml')].write(header)

                header = '<filelists xmlns="http://linux.duke.edu/metadata/filelists" packages="%d">\n' % package_count
                open_files[self.index_filename(state_slug, architecture, 'filelists.xml')].write(header)
                open_files[self.index_filename(state_slug, architecture, 'comps.xml')].write('<!DOCTYPE comps PUBLIC "-//CentOS//DTD Comps info//EN" "comps.dtd">\n')
                open_files[self.index_filename(state_slug, architecture, 'comps.xml')].write('<comps>\n')

                header = '<metadata xmlns="http://linux.duke.edu/metadata/common" xmlns:rpm="http://linux.duke.edu/metadata/rpm" packages="%d">\n' % package_count
                open_files[self.index_filename(state_slug, architecture, 'primary.xml')].write(header)

        # fill all files with RPMs
        for rpm_obj in rpm_objects:
            template_values = self.get_package_template_values(rpm_obj)
            filelists = render_to_string('repositories/yum/filelists.xml', template_values)
            primary = render_to_string('repositories/yum/primary.xml', template_values)
            other = render_to_string('repositories/yum/other.xml', template_values)
            for state_slug in rpm_obj.states:
                architectures = {rpm_obj.header.architecture, }
                if architectures == {'noarch'}:
                    architectures = architectures_by_state[state_slug]
                for architecture in architectures:
                    open_files[self.index_filename(state_slug, architecture, 'filelists.xml')].write(filelists)
                    open_files[self.index_filename(state_slug, architecture, 'primary.xml')].write(primary)
                    open_files[self.index_filename(state_slug, architecture, 'other.xml')].write(other)

        # finish all files
        for state_slug, architectures in architectures_by_state.items():
            for architecture in architectures:
                open_files[self.index_filename(state_slug, architecture, 'other.xml')].write('</otherdata>\n')
                open_files[self.index_filename(state_slug, architecture, 'filelists.xml')].write('</filelists>\n')
                open_files[self.index_filename(state_slug, architecture, 'comps.xml')].write('</comps>\n')
                open_files[self.index_filename(state_slug, architecture, 'primary.xml')].write('</metadata>\n')

        default_architectures = {'amd64', }
        uid = self.storage_uid % repository.id
        repo_slug = repository.slug
        root_url = reverse('%s:index' % self.archive_type, kwargs={'rid': repository.id, })
        if repository.is_private:
            root_url = 'authb-%s' % root_url
        states = [state for state in states if
                  Element.objects.filter(repository=repository, states=state).count() > 0]

        architectures_by_state = set()
        all_states = set()
        open_files = {}
        complete_file_list = {}
        root = 'dists/%(repo)s/' % {'repo': repo_slug}
        # list all available architectures (required to add architecture-independent packages to all archs)
        for element in Element.objects.filter(repository=repository):
            control_data = parse_control_data(element.extra_data)
            architecture = control_data.get('Architecture', 'all')
            architectures_by_state.add(architecture)
            # build the following files:
        #   * dists/(group)/(state)/binary-(architecture)/Packages
        #   * dists/(group)/(state)/binary-(architecture)/Release
        # prepare data for:
        #   * dists/(group)/Contents-(architecture)
        if not architectures_by_state or architectures_by_state == {'all'}:
            architectures_by_state = default_architectures
        for state_slug in states:
            state_architectures = set()
            all_states.add(state_slug.name)
            for element in Element.objects.filter(repository=repository, states=state_slug).order_by('filename'):
                control_data = parse_control_data(element.extra_data)
                architecture = control_data.get('Architecture', 'all')
                section = control_data.get('Section', 'contrib')
                package_file_list = ["%- 100s%s\n" % (x, section) for x in self.file_list(element, uid)]
                if architecture == 'all':
                    elt_architectures = default_architectures
                else:
                    elt_architectures = (architecture,)
                state_architectures |= elt_architectures
                for architecture in elt_architectures:
                    complete_file_list.setdefault(architecture, [])
                    complete_file_list[architecture] += package_file_list

                    filename = 'dists/%(repo)s/%(state)s/binary-%(architecture)s/Packages' % {
                        'repo': repo_slug, 'state': state_slug.name, 'architecture': architecture, }
                    if filename not in open_files:
                        open_files[filename] = tempfile.TemporaryFile(mode='w+b')
                    package_file = open_files[filename]
                    package_file.write(element.extra_data.encode('utf-8'))
                    for key, attr in (('MD5sum', 'md5'), ('SHA1', 'sha1'), ('SHA256', 'sha256'),
                                      ('Size', 'filesize')):
                        if key not in control_data:
                            package_file.write("{0}: {1}\n".format(key, getattr(element, attr)).encode('utf-8'))
                    package_url = reverse('%s:get_file' % self.archive_type,
                                          kwargs={'rid': repository.id, 'repo_slug': repo_slug,
                                                  'filename': element.filename, 'state_slug': state_slug.slug,
                                                  'folder': element.filename[0:1], })
                    package_url = os.path.relpath(package_url, root_url)
                    package_file.write("Filename: {0}\n".format(package_url).encode('utf-8'))
                    package_file.write("\n".encode('utf-8'))
            if len(state_architectures) == 0:
                state_architectures = default_architectures
                # we process elements
            for architecture in state_architectures:
                filename = 'dists/%(repo)s/%(state)s/binary-%(architecture)s/Release' % {
                    'repo': repo_slug, 'state': state_slug.slug, 'architecture': architecture,
                }
                open_files[filename] = tempfile.TemporaryFile(mode='w+b')
                content = render_to_string('repositories/aptitude/architecture_release.txt',
                                           {'architecture': architecture, 'repository': repository, 'state': state_slug, })
                open_files[filename].write(content.encode('utf-8'))
                # build the following files:
        # * dists/(group)/Contents-(architecture)
        for architecture, file_list in complete_file_list.items():
            file_list.sort()
            filename = 'dists/%(repo)s/Contents-%(architecture)s' % {'repo': repo_slug,
                                                                     'architecture': architecture, }
            open_files[filename] = tempfile.TemporaryFile(mode='w+b')
            open_files[filename].write(render_to_string('repositories/aptitude/contents.txt').encode('utf-8'))
            for info in file_list:
                open_files[filename].write(info.encode('utf-8'))
                # build the following files:
        # * dists/(group)/Contents-(architecture).gz/.bz2/.xz
        #   * dists/(group)/(state)/binary-(architecture)/Packages.gz/.bz2/.xz
        #   * dists/(group)/(state)/binary-(architecture)/Release.gz/.bz2/.xz
        # store all files in the cache
        hash_controls = self.compress_files(open_files, root, uid)
        #   * dists/(group)/Release
        # store all files in the cache
        release_file = tempfile.TemporaryFile(mode='w+b')
        now = datetime.datetime.now(tz)
        now_str = now.strftime('%a, %d %b %Y %H:%M:%S %z')  # 'Mon, 29 Nov 2010 08:12:51 UTC'
        until = (now + datetime.timedelta(validity)).strftime('%a, %d %b %Y %H:%M:%S %z')
        content = render_to_string('repositories/aptitude/state_release.txt',
                                   {'architectures': architectures_by_state, 'until': until,
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

        gpg_file = tempfile.TemporaryFile(mode='w+b')
        gpg_file.write(signature.encode('utf-8'))
        gpg_file.flush()
        gpg_file.seek(0)
        filename = 'dists/%(repo)s/Release.gpg' % {'repo': repo_slug, }
        storage(settings.STORAGE_CACHE).store_descriptor(uid, filename, gpg_file)
        gpg_file.close()

    @staticmethod
    def index_filename(state, architecture, name):
        return '%(state)s/%(architecture)s/repodata/%(name)s' % {'state': state.slug, 'architecture': architecture, 'name': name, }
