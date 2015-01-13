#coding=utf-8

from django.conf.urls import patterns, include


def get_patterns():
    from moneta.repository.models import RepositoryModelsClasses
    pattern_list_ = []
    for name, model in RepositoryModelsClasses().get_models().items():
        pattern_list_.append((r'^p/%s/' % name, include(model.public_urls, namespace=name)))
    pattern_list_.append((r'^p/$', 'moneta.repository.views.public_check'))
    for name, model in RepositoryModelsClasses().get_models().items():
        pattern_list_.append((r'^a/%s/' % name, include(model.urls, namespace='auth-' + name)))
        pattern_list_.append((r'^b/%s/' % name, include(model.public_urls, namespace='authb-' + name)))
    pattern_list_.append((r'^a/$', 'moneta.repository.views.private_check'))
    pattern_list_.append((r'^b/$', 'moneta.repository.views.private_check'))
    return pattern_list_


name_set = set()
pattern_list = get_patterns()

urlpatterns = patterns('', *pattern_list)
