# coding=utf-8


from moneta.repository.models import Element, Repository
from django.contrib import admin


class ElementAdmin(admin.ModelAdmin):
    pass


admin.site.register(Element, ElementAdmin)
admin.site.register(Repository)
