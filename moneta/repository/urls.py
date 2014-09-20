#coding=utf-8

from django.utils.six import u

__author__ = u('flanker')

from django.conf.urls import patterns, include

from moneta.repository.models import RepositoryModelsClasses

pattern_list = []
name_set = set()
for name, model in RepositoryModelsClasses().get_models().items():
    pattern_list.append((r'^p/%s/' % name, include(model.public_urls, namespace=name)))
pattern_list.append((r'^p/$', 'moneta.repository.views.public_check'))
for name, model in RepositoryModelsClasses().get_models().items():
    pattern_list.append((r'^a/%s/' % name, include(model.urls, namespace='auth-' + name)))
    pattern_list.append((r'^b/%s/' % name, include(model.public_urls, namespace='authb-' + name)))
pattern_list.append((r'^a/$', 'moneta.repository.views.private_check'))
pattern_list.append((r'^b/$', 'moneta.repository.views.private_check'))

urlpatterns = patterns('', *pattern_list)
