# Generated by Django 1.10.4 on 2016-12-26 22:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('repository', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='repository',
            name='on_index',
            field=models.BooleanField(db_index=True, default=True, verbose_name="Afficher sur l'index public ?"),
        ),
    ]
