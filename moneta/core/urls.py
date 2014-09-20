# coding=utf-8

__author__ = 'flanker'

from django.conf.urls import patterns

urlpatterns = patterns('',
                       (r'^p/$', 'moneta.core.views.public_check'),
                       (r'^p/get/(?P<eid>\d+)/(?P<name>.*)$', 'moneta.core.views.get_file_p'),
                       (r'^p/check/(?P<eid>\d+)/(?P<value>sha1|sha256|md5)$', 'moneta.core.views.get_checksum_p'),
                       (r'^p/signature/(?P<eid>\d+)/(?P<sid>\d+)/$', 'moneta.core.views.get_signature_p'),
                       (r'^a/get/(?P<eid>\d+)/(?P<name>.*)$', 'moneta.core.views.get_file'),
                       (r'^a/check/(?P<eid>\d+)/(?P<value>sha1|sha256|md5)$', 'moneta.core.views.get_checksum'),
                       (r'^a/file/(?P<eid>\d+)/$', 'moneta.core.views.show_file'),
                       (r'^a/add_package/(?P<rid>\d+)/$', 'moneta.core.views.add_element'),
                       (r'^a/post/(?P<rid>\d+)/$', 'moneta.core.views.add_element_post'),
                       (r'^a/sign/(?P<rid>\d+)/$', 'moneta.core.views.add_element_signature'),
                       (r'^a/signature/(?P<eid>\d+)/(?P<sid>\d+)/$', 'moneta.core.views.get_signature'),
                       (r'^a/modify/(?P<rid>\d+)/$', 'moneta.core.views.modify_repository'),
                       (r'^a/delete/(?P<rid>\d+)/$', 'moneta.core.views.delete_repository'),
                       (r'^a/delete/(?P<rid>\d+)/(?P<eid>\d+)/$', 'moneta.core.views.delete_element'),
                       (r'^a/search/(?P<rid>\d+)/$', 'moneta.core.views.search_package'),
                       (r'^a/compare/(?P<rid>\d+)/$', 'moneta.core.views.compare_states'),
                       (r'^a/index/$', 'moneta.core.views.index'),
                       (r'^a/$', 'moneta.core.views.private_check'),
                       (r'^a/check/$', 'moneta.core.views.check'),
                       (r'^test/$', 'moneta.core.views.test_upload'),
                       )
