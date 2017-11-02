from django.conf.urls import url
from moneta.views import public_check, index, check, add_element, add_element_post, add_element_signature, \
    get_signature, modify_repository, delete_repository, delete_element, search_package, compare_states, private_check, \
    test_upload, get_file_p, get_checksum_p, get_signature_p, get_file, get_checksum, show_file


__author__ = 'flanker'

urlpatterns = [
    url(r'^p/$', public_check, name='public_check'),
    url(r'^p/get/(?P<eid>\d+)/(?P<name>.*)$', get_file_p, name='get_file_p'),
    url(r'^p/check/(?P<eid>\d+)/(?P<value>sha1|sha256|md5)$', get_checksum_p, name='get_checksum_p'),
    url(r'^p/signature/(?P<eid>\d+)/(?P<sid>\d+)/$', get_signature_p, name='get_signature_p'),
    url(r'^a/get/(?P<eid>\d+)/(?P<name>.*)$', get_file, name='get_file'),
    url(r'^a/check/(?P<eid>\d+)/(?P<value>sha1|sha256|md5)$', get_checksum, name='get_checksum'),
    url(r'^a/file/(?P<eid>\d+)/$', show_file, name='show_file'),
    url(r'^a/add_package/(?P<rid>\d+)/$', add_element, name='add_element'),
    url(r'^a/post/(?P<rid>\d+)/$', add_element_post, name='add_element_post'),
    url(r'^a/sign/(?P<rid>\d+)/$', add_element_signature, name='add_element_signature'),
    url(r'^a/signature/(?P<eid>\d+)/(?P<sid>\d+)/$', get_signature, name='get_signature'),
    url(r'^a/modify/(?P<rid>\d+)/$', modify_repository, name='modify_repository'),
    url(r'^a/delete/(?P<rid>\d+)/$', delete_repository, name='delete_repository'),
    url(r'^a/delete/(?P<rid>\d+)/(?P<eid>\d+)/$', delete_element, name='delete_element'),
    url(r'^a/search/(?P<rid>\d+)/$', search_package, name='search_package'),
    url(r'^a/compare/(?P<rid>\d+)/$', compare_states, name='compare_states'),
    url(r'^a/index/$', index, name='index'),
    url(r'^a/$', private_check, name='private_check'),
    url(r'^a/check/$', check, name='check'),
    url(r'^test/$', test_upload, name='test_upload'),

]
app_name = 'moneta'
