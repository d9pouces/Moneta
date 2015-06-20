# -*- coding: utf-8 -*-
import pkg_resources

from moneta.repositories.tests import RepositoryTestCase
from moneta.repositories.yum import Yum

__author__ = 'flanker'


class TestYumRpm(RepositoryTestCase):

    def test_add_file(self):
        repo = self.create_repository(Yum)
        filename = pkg_resources.resource_filename('moneta.repositories.tests', '389-ds-base-libs-1.3.3.1-13.el7.x86_64.rpm')
        self.add_file_to_repository(repo, filename)

    def test_generate_index(self):
        repo = self.create_repository(Yum)
        filename = pkg_resources.resource_filename('moneta.repositories.tests', '389-ds-base-libs-1.3.3.1-13.el7.x86_64.rpm')
        self.add_file_to_repository(repo, filename)
        yum = Yum()
        yum.generate_indexes(repo)
