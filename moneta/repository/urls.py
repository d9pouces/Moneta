
from django.conf.urls import include, url
from moneta.repository import views


def get_patterns():
    from moneta.repositories.base import RepositoryModelsClasses
    pattern_list_ = []
    for name, model in RepositoryModelsClasses().get_models().items():
        pattern_list_.append(url(r'^p/%s/' % name, (model.public_urls, name, name)))
    pattern_list_.append(url(r'^p/$', views.public_check, name='public_check'))
    for name, model in RepositoryModelsClasses().get_models().items():
        pattern_list_.append(url(r'^a/%s/' % name, (model.urls, 'auth-' + name, 'auth-' + name)))
        pattern_list_.append(url(r'^b/%s/' % name, (model.public_urls, 'authb-' + name, 'authb-' + name)))
    pattern_list_.append(url(r'^a/$', views.private_check, name='private_check_a'))
    pattern_list_.append(url(r'^b/$', views.private_check, name='private_check_b'))
    return pattern_list_


name_set = set()
urlpatterns = get_patterns()
app_name = 'repository'
