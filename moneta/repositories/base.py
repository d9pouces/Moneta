from django.http import HttpResponseBadRequest

__author__ = 'flanker'
from django.utils.translation import ugettext_lazy as _
from django.conf.urls import patterns


class RepositoryModel(object):
    verbose_name = _('Repository')
    archive_type = 'RepositoryModel'

    def __str__(self):
        """
        returns a unicode representation of this repository
        :return: unicode representation
        """
        return self.verbose_name

    def is_file_valid(self, uploaded_file):
        """ Evaluate if the uploaded file is valid for this repository model
        :param uploaded_file:
        :return: True if this element is acceptable for this model, else False
        :raise:
        """
        return True

    def delete_element(self, rel):
        pass

    def element(self, element):
        """
        Extract some informations from element to prepare the repository
        :param element: Element to add to the repository
        :return: Unicode string containing meta-data
        """
        return ''

    def url_list(self):
        """
        Return a list of URL patterns specific to this repository
        :return: a patterns as expected by django
        """
        return []

    def public_url_list(self):
        return []

    # noinspection PyMethodMayBeStatic
    def get_index_view(self, repo):
        return repo.model + ':index'

    def wrap_view(self, view, csrf_exempt=False):
        def wrapper(request, *args, **kwargs):
            try:
                return getattr(self, view)(request, *args, **kwargs)
            except AttributeError:
                return HttpResponseBadRequest()
        if csrf_exempt:
            wrapper.csrf_exempt = True
        return wrapper

    def extra_index_urls(self, request, rid):
        """ Provides an iterable of tuples (URL, name), to add on the main index
        :param request: HttpRequest
        :param rid: Repository id
        """
        return []

    @property
    def urls(self):
        """
        Provides URLconf details for the ``Api`` and all registered
        ``Resources`` beneath it.
        """
        pattern_list = self.url_list()
        urlpatterns = patterns('', *pattern_list)
        return urlpatterns

    @property
    def public_urls(self):
        pattern_list = self.public_url_list()
        urlpatterns = patterns('', *pattern_list)
        return urlpatterns

    def index_base(self, request, name, rid):
        """
        Return a HttpResponse
        :param request: HttpRequest
        :raise:
        """
        raise NotImplementedError
