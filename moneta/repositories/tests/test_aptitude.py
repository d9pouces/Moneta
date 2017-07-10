import pkg_resources
from moneta.repositories.aptitude import Aptitude
from moneta.repositories.tests import RepositoryTestCase

__author__ = 'flanker'


class TestYumRpm(RepositoryTestCase):

    def test_add_file(self):
        repo = self.create_repository(Aptitude)
        filename = pkg_resources.resource_filename('moneta.repositories.tests', 'lib3ds-dev_1.3.0-8_mips.deb')
        self.add_file_to_repository(repo, filename)

    def test_generate_index(self):
        repo = self.create_repository(Aptitude)
        filename = pkg_resources.resource_filename('moneta.repositories.tests', 'lib3ds-dev_1.3.0-8_mips.deb')
        self.add_file_to_repository(repo, filename)
        aptitude = Aptitude()
        aptitude.generate_indexes(repo)
