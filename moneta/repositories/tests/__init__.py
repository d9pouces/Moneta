import os
from django.contrib.auth.models import User
from django.core.files.uploadedfile import UploadedFile
from django.http import HttpRequest, HttpResponse
from django.test import TestCase
from moneta.repositories.base import RepositoryModel
from moneta.repository.models import Repository, ArchiveState
from moneta.views import generic_add_element

__author__ = 'flanker'


class RepositoryTestCase(TestCase):

    def get_request(self):
        user = User.objects.get_or_create(username='test_user')[0]
        request = HttpRequest()
        request.user = user
        return request

    def create_repository(self, repo_cls, name='test_repo', author=None, states='qualif prod'):
        assert issubclass(repo_cls, RepositoryModel)
        if author is None:
            author = User.objects.get_or_create(username='test_user')[0]
        repo = Repository(author=author, name=name, on_index=True, archive_type=repo_cls.archive_type, is_private=False)
        repo.save()
        for state in states.split():
            ArchiveState(repository=repo, name=state, author=author).save()
        return repo

    def add_file_to_repository(self, repo, filename, states=None, name='', archive='', version=''):
        if states is None:
            states = ['qualif', 'prod', ]
        uploaded_file = UploadedFile(name=os.path.basename(filename), file=open(filename, 'rb'))
        request = self.get_request()
        element = generic_add_element(request, repo, uploaded_file, states, name=name, archive=archive, version=version, )
        return element
