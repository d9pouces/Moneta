# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repository', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='repository',
            name='is_public',
        ),
        migrations.AlterField(
            model_name='repository',
            name='archive_type',
            field=models.CharField(db_index=True, choices=[('maven3', 'Maven repository for Java packages'), ('pypy', 'Pypi repository for Python packages'), ('aptitude', 'APT repository for Linux .deb packages')], max_length=100, verbose_name='Type de dépôt'),
        ),
    ]
