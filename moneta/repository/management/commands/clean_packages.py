# coding=utf-8
from django.core.management import BaseCommand
from moneta.repository.models import Element

__author__ = 'flanker'


class Command(BaseCommand):
    def handle(self, *args, **options):
        for elt in Element.objects.all():
            elt.delete()
