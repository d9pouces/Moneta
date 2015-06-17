# -*- coding: utf-8 -*-
from django.http import HttpRequest
from django.test import TestCase
from moneta.repositories.maven3 import Maven3
from moneta.repository.models import Repository, Element

__author__ = 'flanker'


class TestMaven3(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.repo = Repository(archive_type=Maven3.archive_type, name='test_maven3')
        cls.repo.save()
        cls.elts = [
            Element(version='1.1.4c',
                    archive='xpp3.xpp3_min',
                    name='xpp3_min',
                    filename='xpp3_min-1.1.4c.jar',
                    full_name='xpp3_min-1.1.4c.jar',
                    sha1='19d4e90b43059058f6e056f794f0ea4030d60b86', ),
            Element(version='1.0-2',
                    archive='javax.xml.stream.stax-api',
                    name='stax-api',
                    filename='stax-api-1.0-2.jar',
                    full_name='stax-api-1.0-2.jar',
                    sha1='d6337b0de8b25e53e81b922352fbea9f9f57ba0b', ),
            Element(version='1.0-2',
                    archive='javax.xml.stream.stax-api',
                    name='stax-api',
                    filename='stax-api-1.0-2.pom',
                    full_name='stax-api-1.0-2.pom',
                    sha1='5379b69f557c5ab7c144d22bf7c3768bd2adb93d', ),
            Element(version='2.2.2',
                    archive='javax.xml.bind.jaxb-api',
                    name='jaxb-api',
                    filename='jaxb-api-2.2.2.jar',
                    full_name='jaxb-api-2.2.2.jar',
                    sha1='aeb3021ca93dde265796d82015beecdcff95bf09', ),
            Element(version='2.2.2',
                    archive='javax.xml.bind.jaxb-api',
                    name='jaxb-api',
                    filename='jaxb-api-2.2.2.pom',
                    full_name='jaxb-api-2.2.2.pom',
                    sha1='a8368234f7555dd64d3a9060a0b02e6c215694fb', ),
        ]
        for elt in cls.elts:
            elt.repository = cls.repo
        Element.objects.bulk_create(cls.elts)

    def test_count(self):
        self.assertEqual(Element.objects.filter(repository=self.repo).count(), 5)

    def test_xpp3(self):
        self.assertEqual(len(Maven3.browse_repo_inner(self.repo.id, 'xpp3')), 1)
        self.assertEqual(len(Maven3.browse_repo_inner(self.repo.id, 'xpp3/xpp3_min')), 1)
        self.assertEqual(len(Maven3.browse_repo_inner(self.repo.id, 'xpp3/xpp3_m')), 0)
        self.assertEqual(len(Maven3.browse_repo_inner(self.repo.id, 'xpp3/xpp3_min/1.1.4')), 0)
        self.assertEqual(len(Maven3.browse_repo_inner(self.repo.id, 'xpp3/')), 1)
        self.assertEqual(len(Maven3.browse_repo_inner(self.repo.id, 'xpp3/xpp3_min/')), 1)
        self.assertEqual(len(Maven3.browse_repo_inner(self.repo.id, 'xpp3/xpp3_min/1.1.4')), 0)
        self.assertEqual(len(Maven3.browse_repo_inner(self.repo.id, 'xpp3/xpp3_min/1.1.4c')), 1)
        self.assertEqual(len(Maven3.browse_repo_inner(self.repo.id, 'xpp3/xpp3_min/1.1.4c/')), 1)
        self.assertIsInstance(Maven3.browse_repo_inner(self.repo.id, 'xpp3/xpp3_min/1.1.4c/xpp3_min-1.1.4c.jar'), Element)
        self.assertIsInstance(Maven3.browse_repo_inner(self.repo.id, 'xpp3/xpp3_min/1.1.4c/xpp3_min-1.1.4c.jar.sha1'), str)
        self.assertEqual(Maven3.browse_repo_inner(self.repo.id, 'xpp3/xpp3_min/1.1.4c/xpp3_min-1.1.4c.jar.sha1'),
                         '19d4e90b43059058f6e056f794f0ea4030d60b86')
        self.assertEqual(Element.objects.filter(repository=self.repo).count(), 5)

    def test_javax(self):
        result = Maven3.browse_repo_inner(self.repo.id, 'javax')
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result, dict)
        self.assertTrue('javax' in result)

    def test_all(self):
        result = Maven3.browse_repo_inner(self.repo.id, '')
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result, dict)
        self.assertTrue('javax' in result)
        self.assertTrue('xpp3' in result)
