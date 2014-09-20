#coding=utf-8

from django.utils.six import u

__author__ = u('flanker')


from tastypie import fields
from tastypie.authorization import DjangoAuthorization
from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from moneta.repository.models import Choice, Poll


class PollResource(ModelResource):

    class Meta:
        queryset = Poll.objects.all()
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get', 'post', 'put', 'delete']
        resource_name = 'poll'
        authorization = DjangoAuthorization()
        filtering = {'question': ALL, 'pub_date': ['exact', 'range', 'gt', 'gte', 'lt', 'lte'], }


class ChoiceResource(ModelResource):
    poll = fields.ForeignKey(PollResource, 'poll')

    class Meta:
        queryset = Choice.objects.all()
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get', 'post', 'put', 'delete']
        resource_name = 'poll_resource'
        authorization = DjangoAuthorization()
        filtering = {'choice_text': ALL, 'votes': ['exact', 'range', 'gt', 'gte', 'lt', 'lte'], }
