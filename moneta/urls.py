# -*- coding=utf-8 -*-

__author__ = 'flanker'

from django.conf.urls import patterns

urlpatterns = patterns('',
                       (r'^p/$', 'moneta.views.public_check'),
                       (r'^p/get/(?P<eid>\d+)/(?P<name>.*)$', 'moneta.views.get_file_p'),
                       (r'^p/check/(?P<eid>\d+)/(?P<value>sha1|sha256|md5)$', 'moneta.views.get_checksum_p'),
                       (r'^p/signature/(?P<eid>\d+)/(?P<sid>\d+)/$', 'moneta.views.get_signature_p'),
                       (r'^a/get/(?P<eid>\d+)/(?P<name>.*)$', 'moneta.views.get_file'),
                       (r'^a/check/(?P<eid>\d+)/(?P<value>sha1|sha256|md5)$', 'moneta.views.get_checksum'),
                       (r'^a/file/(?P<eid>\d+)/$', 'moneta.views.show_file'),
                       (r'^a/add_package/(?P<rid>\d+)/$', 'moneta.views.add_element'),
                       (r'^a/post/(?P<rid>\d+)/$', 'moneta.views.add_element_post'),
                       (r'^a/sign/(?P<rid>\d+)/$', 'moneta.views.add_element_signature'),
                       (r'^a/signature/(?P<eid>\d+)/(?P<sid>\d+)/$', 'moneta.views.get_signature'),
                       (r'^a/modify/(?P<rid>\d+)/$', 'moneta.views.modify_repository'),
                       (r'^a/delete/(?P<rid>\d+)/$', 'moneta.views.delete_repository'),
                       (r'^a/delete/(?P<rid>\d+)/(?P<eid>\d+)/$', 'moneta.views.delete_element'),
                       (r'^a/search/(?P<rid>\d+)/$', 'moneta.views.search_package'),
                       (r'^a/compare/(?P<rid>\d+)/$', 'moneta.views.compare_states'),
                       (r'^a/index/$', 'moneta.views.index'),
                       (r'^a/$', 'moneta.views.private_check'),
                       (r'^a/check/$', 'moneta.views.check'),
                       (r'^test/$', 'moneta.views.test_upload'),
                       )
