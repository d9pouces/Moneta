# -*- coding=utf-8 -*-
"""
Emulate a Maven3-compatible repository.


/$groupId[0]/../${groupId[n]/$artifactId/$version/$artifactId-$version.$extension
/$groupId[0]/../$groupId[n]/$artifactId/$version/$artifactId-$version-$classifier.$extension
/org/codehaus/plexus/plexus-container/0.15/
                     /plexus-container-0.15.jar
                     /plexus-container-0.15.jar.md5
                     /plexus-container-0.15.pom
                     /plexus-container-0.15.pom.md5
                     /plexus-container-0.15-javadoc.jar
                     /plexus-container-0.15-javadoc.jar.md5
                     /plexus-container-0.15-javasrc.jar
                     /plexus-container-0.15-javasrc.jar.md5

Maven3 variables:
    * $groupId = org.codehaus.plexus
    * $artifactId = plexus-container
    * $version = 0.15
    * $extension = jar
    * $classifier = javadoc, javasrc

Moneta mapping:
    * element.version maps to $version
    * element.archive maps to $groupId.$artifactId
    * element.name maps to $artifactId => built from element.archive
    * element.filename maps to $artifactId-$version-$classifier.$extension
    * element.full_name = element.filename

Command for uploading files:
curl --data-binary @$FILENAME http://[...]/\?filename=$FILENAME\&states=prod\&states=qualif\&archive=$groupId.$artifactId\&version=$version

URLs to emulate:
    /$groupId[0]/../$groupId[n]/$artifactId/$version/(filename)$
    /$groupId[0]/../$groupId[n]/$artifactId/$version/(filename).md5$
    /$groupId[0]/../$groupId[n]/$artifactId/$version/(filename).sha1$
    /$groupId[0]/../$groupId[n]/$artifactId/$version/(filename).sha256$
"""
import os.path
import zipfile

from django.conf import settings
from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string

from django.utils.translation import ugettext as _
from moneta.templatetags.moneta import moneta_url

from moneta.utils import parse_control_data
from moneta.repositories.aptitude import Aptitude
from moneta.repository.models import storage, Repository, Element, ArchiveState
from moneta.views import get_file

__author__ = 'flanker'


class Maven3(Aptitude):
    verbose_name = _('Maven repository for Java packages')
    storage_uid = '94633000-0000-0000-0000-%012d'
    archive_type = 'maven3'

    def is_file_valid(self, uploaded_file):
        return True

    def update_element(self, element):
        """
        Extract some informations from element to prepare the repository
        :param element: Element to add to the repository
        :return: Unicode string containing meta-data

        ar -x control.tar.gz
        tar -xf control.tar.gz control
        """
        if element.archive:
            element.name = element.archive.rpartition('.')[2]
        if element.filename.endswith('.jar') and False:
            archive_file = storage(settings.STORAGE_ARCHIVE).get_file(element.archive_key)

            compressed_file = zipfile.ZipFile(archive_file)
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
                              ('Name', 'name'), ):
                if key in control_data:  # archive : PackageName, name : Organization Name
                    setattr(element, attr, control_data.get(key, ''))
            # element.filename = '%s-%s.jar' % (element.archive.rpartition('.')[2], element.version)

    @staticmethod
    def browse_repo_inner(rid: int, query_string: str, state_slug: str=None):
        """should only called from browse_repository()

        :param rid:
        :param query_string: a single str corresponding to $groupId/$artifactId/$version/$filename.$extension
        :return:
            a string -> send it in a HttpResponse
            an Element -> send it with views.get_file
            a dict -> {"net": {"19pouces": {"moneta": {"1.6.0": {set of <Element>}, }, }, }
        """
        if query_string[-1:] == '/':
            query_string = query_string[:-1]
        state = get_object_or_404(ArchiveState, repository__id=rid, name=state_slug) if state_slug else None
        gav, sep, filename = query_string.rpartition('/')
        dotted_gavf = query_string.replace('/', '.')
        if sep == '/':
            group_artifact, sep, version = gav.rpartition('/')
            group_artifact = group_artifact.replace('/', '.')
            dotted_gav = gav.replace('/', '.')
            if sep == '/':
                # URL: "gro/up/arti/fact/version/filename*"
                # URL: "gro/up/arti/fact/version*"
                # URL: "gro/up/arti/fact*"
                no_ext, sep, ext = filename.rpartition('.')
                if ext not in ('sha1', 'sha256', 'md5') and sep == '.':
                    no_ext = filename
                query = Element.objects.filter(
                    Q(archive=group_artifact, version=version, filename=no_ext) |
                    Q(archive=dotted_gav, version=filename) |
                    Q(archive=dotted_gavf) | Q(archive__startswith=dotted_gavf + '.')
                )
            else:
                # URL: "group_artifact/version"
                query = Element.objects.filter(
                    Q(archive=dotted_gav, version=filename) |
                    Q(archive=dotted_gavf) | Q(archive__startswith=dotted_gavf + '.')
                )
        else:
            # URL: "group_artifact"
            query = Element.objects.filter(archive__startswith=dotted_gavf)
        query = query.filter(repository__id=rid)
        if state:
            query = query.filter(states=state)
        no_ext, sep, ext = query_string.rpartition('.')
        if ext not in ('sha1', 'sha256', 'md5') and sep == '.':
            no_ext = query_string

        # ok, we have to check
        results = {}
        for elt in query:
            elt_gavf = '%s/%s/%s' % (elt.archive.replace('.', '/'), elt.version, elt.filename)

            if elt_gavf == no_ext:
                if ext in ('sha1', 'sha256', 'md5'):
                    return getattr(elt, ext)
                return elt
            elt_gav = '%s/%s' % (elt.archive.replace('.', '/'), elt.version)
            if elt_gav == query_string:
                pass
            parents_results = results
            for path_comp in elt.archive.split('.'):
                parents_results = parents_results.setdefault(path_comp, {})
            parents_results.setdefault(elt.version, set()).add(elt)
        return results

    def browse_repository(self, request: HttpRequest, rid: int, repo_slug: str, query_string: str='', state_slug: str=None) -> HttpResponse:
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.archive_type)
        result = self.browse_repo_inner(rid, query_string, state_slug=state_slug)
        if isinstance(result, str):  # sha1/sha256/md5
            return HttpResponse(result)
        elif isinstance(result, Element):
            return get_file(request, eid=result.pk, element=result)
        assert isinstance(result, dict)

        new_query_string = ''
        bread_crumbs = [(_('Root'), self.get_browse_url(repo, new_query_string))]
        while len(result) == 1 and isinstance(result, dict):
            path_component, result = result.popitem()
            new_query_string += path_component + '/'
            bread_crumbs.append((path_component, self.get_browse_url(repo, new_query_string)))
        if isinstance(result, set):
            url_list = []
            for elt in result:
                new_gavf_elt_filename = new_query_string + elt.filename
                elt_url = self.get_browse_url(repo, new_gavf_elt_filename)
                url_list += [(new_gavf_elt_filename, elt_url),
                           (new_gavf_elt_filename + '.sha1', elt_url + '.sha1'),
                           (new_gavf_elt_filename + '.sha256', elt_url + '.sha256'),
                           (new_gavf_elt_filename + '.md5', elt_url + '.md5'),
                ]
        else:
            assert isinstance(result, dict)
            url_list = [(new_query_string + key, self.get_browse_url(repo, new_query_string + key))
                        for key in result]
        template_values = {'repo': repo, 'admin_allowed': repo.admin_allowed(request), 'repo_slug': repo_slug, 'admin': True,
                           'paths': url_list, 'request_path': new_query_string,
                           'bread_crumbs': bread_crumbs, }
        return render_to_response('repositories/maven3/browse.html', template_values, RequestContext(request))

    @staticmethod
    def get_browse_url(repo, new_query_string):
        browse_view_name = moneta_url(repo, 'browse')
        return reverse(browse_view_name, kwargs={'rid': repo.id, 'repo_slug': repo.slug, 'query_string': new_query_string})

    def public_url_list(self):
        """
        Return a list of URL patterns specific to this repository
        Sample recognized urls:
            /$groupId[0]/../$groupId[n]/$artifactId/$version/(filename)(|.md5|sha1|sha256)$
            r'^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]+)/(?P<gav>.+)/(?P<filename>[^/]+)$'
            '
        :return: a patterns as expected by django

        """

        # http://mvnrepository.com/artifact/org.requs/requs-exec/1.11
        pattern_list = [
            url(r'^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]+)/browse/(?P<query_string>.*)$', self.wrap_view('browse_repository'), name='browse'),
            url(r'^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]+)/s/(?P<state_slug>[\w\-\._]+)/browse/(?P<query_string>.*)$', self.wrap_view('browse_repository'), name='browse'),
            url(r'^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]+)/browse/$', self.wrap_view('browse_repository'), name='browse'),
            url(r'^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]+)/s/(?P<state_slug>[\w\-\._]+)/browse/$', self.wrap_view('browse_repository'), name='browse'),
            url(r"^(?P<rid>\d+)/$", self.wrap_view('index'), name="index"),
        ]
        return pattern_list

    def index(self, request, rid):
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.archive_type)
        states = list(ArchiveState.objects.filter(repository=repo).order_by('name'))
        template_values = {'repo': repo, 'states': states, 'admin_allowed': repo.admin_allowed(request)}
        state_infos = []
        template_values['state_slug'] = None
        request_context = RequestContext(request)
        setting_str = render_to_string('repositories/maven3/maven_settings.xml', template_values, request_context)

        state_infos.append(('all-packages', str(setting_str), _('All states'), states))
        for state in states:
            template_values['state_slug'] = state.slug
            setting_str = render_to_string('repositories/maven3/maven_settings.xml', template_values, request_context)
            state_infos.append((state.slug, str(setting_str), state.name, [state]))
        template_values['state_infos'] = state_infos
        return render_to_response('repositories/maven3/index.html', template_values, request_context)
