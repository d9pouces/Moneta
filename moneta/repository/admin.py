#coding=utf-8

from django.utils.six import u

from moneta.repository.models import Element, Repository


__author__ = u('flanker')


from django.contrib import admin


class ElementAdmin(admin.ModelAdmin):
    pass


admin.site.register(Element, ElementAdmin)
admin.site.register(Repository)
