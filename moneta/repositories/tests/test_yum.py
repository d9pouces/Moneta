# -*- coding: utf-8 -*-
from django.test import TestCase
import pkg_resources
from pyrpm import rpm

__author__ = 'flanker'




class TestYumRpm(TestCase):
    def test_values(self):
        fd = pkg_resources.resource_stream('moneta.repositories.tests', '389-ds-base-libs-1.3.3.1-13.el7.x86_64.rpm')
        rpm_obj = rpm.RPM(fd)