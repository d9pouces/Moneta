import os.path
import zipfile

from django.conf import settings

from django.conf.urls import url
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.timezone import get_current_timezone
from django.utils.translation import ugettext as _

from moneta.utils import parse_control_data

from moneta.repositories.aptitude import Aptitude
from moneta.repositories.xmlrpc import XMLRPCSite
from moneta.repository.models import storage, Repository, Element, ArchiveState


__author__ = 'flanker'

tz = get_current_timezone()
XML_RPC_SITE = XMLRPCSite()


class Maven3(Aptitude):
    verbose_name = _('Maven repository for Java packages')
    storage_uid = '94633000-0000-0000-0000-%012d'
    archive_type = 'maven3'

    def is_file_valid(self, uploaded_file):
        return True

    def element(self, element):
        """
        Extract some informations from element to prepare the repository
        :param element: Element to add to the repository
        :return: Unicode string containing meta-data

        ar -x control.tar.gz
        tar -xf control.tar.gz control
        """
        if element.filename.endswith('.jar'):
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

    def public_url_list(self):
        """
        Return a list of URL patterns specific to this repository
        Sample recognized urls:
            *

        :return: a patterns as expected by django

        """

        # http://mvnrepository.com/artifact/org.requs/requs-exec/1.11
        pattern_list = [
            # url(r"^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]*)/s/(?P<state_slug>[\w\-\._]+)/artifact/(?P<name>[\w\._\-]+)/"
            # r"(?P<archive>[\w\._\-]+)/(?P<version>[\w\._\-]+)/(?P<filename>.*)$",
            #     self.wrap_view('get_filename'), name="get_file"),

            url(r'^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]+)/s/(?P<state_slug>[\w\-\._]+)/artifact/(?P<value>[\w\-/\.]*)$',
                self.wrap_view('browse'), name='browse'),
            url(r'^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]+)/s/(?P<state_slug>[\w\-\._]+)/artifact/$',
                self.wrap_view('browse'), name='browse'),
            url(r'^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]+)/artifact/(?P<value>[\w\-/\.]*)$', self.wrap_view('browse'),
                name='browse'),
            url(r'^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]+)/artifact/$', self.wrap_view('browse'),
                name='browse'),

            # url(r"^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]*)/s/(?P<state_slug>[\w\-\._]+)/artifact/(?P<name>[\w\._\-]+)/"
            #     r"(?P<archive>[\w\._\-]+)/(?P<version>[\w\._\-]+)/$", self.wrap_view('browse'), name="browse"),
            # url(r"^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]*)/s/(?P<state_slug>[\w\-\._]+)/artifact/(?P<name>[\w\._\-]+)/"
            #     r"(?P<archive>[\w\._\-]+)/$", self.wrap_view('browse'), name="browse"),
            # url(r"^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]*)/s/(?P<state_slug>[\w\-\._]+)/artifact/(?P<name>[\w\._\-]+)/$",
            #     self.wrap_view('browse'), name="browse"),
            # url(r"^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]*)/s/(?P<state_slug>[\w\-\._]+)/artifact/$",
            #     self.wrap_view('browse'), name="browse"),
            # url(r"^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]*)/artifact/(?P<name>[\w\._\-]+)/"
            #     r"(?P<archive>[\w\._\-]+)/(?P<version>[\w\._\-]+)/(?P<filename>.*)$",
            #     self.wrap_view('get_filename'), name="get_file"),
            # url(r"^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]*)/artifact/(?P<name>[\w\._\-]+)/"
            #     r"(?P<archive>[\w\._\-]+)/(?P<version>[\w\._\-]+)/$", self.wrap_view('browse'), name="browse"),
            # url(r"^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]*)/artifact/(?P<name>[\w\._\-]+)/"
            #     r"(?P<archive>[\w\._\-]+)/$", self.wrap_view('browse'), name="browse"),
            # url(r"^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]*)/artifact/(?P<name>[\w\._\-]+)/$",
            #     self.wrap_view('browse'), name="browse"),
            # url(r"^(?P<rid>\d+)/(?P<repo_slug>[\w\-\._]*)/artifact/$",
            #     self.wrap_view('browse'), name="browse"),


            url(r"^(?P<rid>\d+)/$", self.wrap_view('index'), name="index"),
        ]
        return pattern_list

    def browse(self, request, rid, repo_slug, state_slug=None, value=''):
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.archive_type)
        request_path = os.path.abspath('/' + value)[1:]
        components = list(filter(lambda x: x, request_path.split('/')))
        base_query = Element.objects.filter(repository=repo)
        if state_slug:
            state = get_object_or_404(ArchiveState.objects.filter(repository=repo), slug=state_slug)
            base_query = base_query.filter(states=state)
        queries = [{'archive__istartswith': '.'.join(components)}]
        if len(components) >= 2:
            queries.append({'archive__iexact': '.'.join(components[0:-1]), 'name__istartswith': components[-1], })
            queries.append({'archive__iexact': '.'.join(components[0:-1]), 'version__istartswith': components[-1], })
        if len(components) >= 3:
            queries.append({'archive__iexact': '.'.join(components[0:-2]), 'name__iexact': components[-2],
                            'version__istartswith': components[-1], })
        if len(components) >= 4:
            elements = base_query.filter(archive__iexact='.'.join(components[0:-3]), name__iexact=components[-3],
                                         version__iexact=components[-2], filename=components[-1])[0:1]
            elements = list(elements)
            if elements:
                from moneta.views import get_file
                return get_file(request, None, element=elements[0])
        all_paths = set()
        for sub_query in queries:
            for element in base_query.filter(**sub_query):
                all_paths.add(self.element_to_path(element, request_path))
        all_paths = list(filter(lambda x: x, all_paths))
        all_paths.sort()
        values = [(x, os.path.dirname(x)) for x in all_paths]
        if request_path:
            values.insert(0, (os.path.join(request_path, '..'), '..'))
        template_values = {'repo': repo, 'admin_allowed': repo.admin_allowed(request), 'repo_slug': repo_slug, 'admin': True,
                           'paths': values, 'request_path': request_path}
        return render_to_response('repositories/maven3/browse.html', template_values, RequestContext(request))

    @staticmethod
    def element_to_path(element, request_path):
        """ renvoie le chemin à afficher dans la liste
        """
        element_components = element.archive.split('.')
        element_components += [element.name, element.version, element.filename]
        request_components = request_path.split('/')
        element_components = list(filter(lambda x: x, element_components))
        print(element_components)

        if len(request_components) > len(element_components):
            return None
        elif not request_components:
            return '%s/' % element_components[0]
        index = len(request_components) - 1
        if element_components[index] == request_components[index]:
            selection = element_components[0:index + 2]
        else:
            selection = element_components[0:index + 1]
        result = '/'.join(selection)
        if len(element_components) > len(request_components) + 1:
            result += '/'
        return result

    def index(self, request, rid):
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.archive_type)
        states = ArchiveState.objects.filter(repository=repo).order_by('name')
        template_values = {'repo': repo, 'states': states, 'admin_allowed': repo.admin_allowed(request)}
        maven_settings_xml = []
        template_values['state_slug'] = None
        request_context = RequestContext(request)
        setting_str = render_to_string('repositories/maven3/maven_settings.xml', template_values, request_context)
        maven_settings_xml.append(('all-packages', str(setting_str)))
        for state in states:
            template_values['state_slug'] = state.slug
            setting_str = render_to_string('repositories/maven3/maven_settings.xml', template_values, request_context)
            maven_settings_xml.append((state.slug, str(setting_str), ))
        template_values['maven_settings_xml'] = maven_settings_xml
        template_values['admin'] = True
        return render_to_response('repositories/maven3/index.html', template_values, request_context)

    # noinspection PyUnusedLocal
    def folder_index(self, request, rid, repo_slug, state_slug=None, name=None, archive=None, version=None):
        """
        Return a HttpResponse
        :param request: HttpRequest
        :raise:
        """
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.archive_type)
        if state_slug:
            state = get_object_or_404(ArchiveState, repository=repo, slug=state_slug)
            query = Element.objects.filter(repo=repo, states=state)
        else:
            query = Element.objects.filter(repo=repo)
        if archive is not None:
            query = query.filter(archive=archive)
        if name is not None:
            query = query.filter(name=name)
        if version is not None:
            query = query.filter(version=version)
        element_query = query.select_related()[0:100]
        element_count = query.count()
        template_values = {'repo': repo, 'state': state_slug, 'element_count': element_count,
                           'admin_allowed': repo.admin_allowed(request),
                           'elements': element_query, 'name': name, 'archive': archive, 'version': version, }
        return render_to_response('repositories/maven3/folder_index.html', template_values,
                                  RequestContext(request))

    # noinspection PyUnusedLocal
    def get_filename(self, request, rid, repo_slug, state_slug, name, archive, version, filename):
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.archive_type)
        state = get_object_or_404(ArchiveState, repository=repo, slug=state_slug)
        element = get_object_or_404(Element, repository=repo, states=state, name=name, archive=archive,
                                    version=version, filename=filename)
        from moneta.core.views import get_file

        return get_file(request, None, element=element)
