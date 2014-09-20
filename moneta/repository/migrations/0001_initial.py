# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArchiveState',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('name', models.CharField(max_length=100, verbose_name='Nom', db_index=True)),
                ('slug', models.SlugField(max_length=100, verbose_name='Nom raccourci')),
                ('creation', models.DateTimeField(db_index=True, auto_now_add=True, verbose_name='Date de création')),
                ('modification', models.DateTimeField(auto_now=True, db_index=True, verbose_name='Date de modification')),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL, blank=True, verbose_name='Auteur', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Element',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('name', models.CharField(max_length=100, verbose_name='Nom', db_index=True)),
                ('slug', models.SlugField(max_length=100, verbose_name='Nom raccourci')),
                ('creation', models.DateTimeField(db_index=True, auto_now_add=True, verbose_name='Date de création')),
                ('modification', models.DateTimeField(auto_now=True, db_index=True, verbose_name='Date de modification')),
                ('official_link', models.URLField(max_length=255, blank=True, verbose_name='URL pour la page web')),
                ('short_description', models.CharField(max_length=500, blank=True, verbose_name='Description courte')),
                ('long_description', models.TextField(blank=True, verbose_name='Description longue')),
                ('full_name', models.CharField(max_length=255, blank=True, verbose_name='Nom complet', db_index=True)),
                ('full_name_normalized', models.CharField(max_length=255, help_text='Nom complet, sans caractères spéciaux', blank=True, verbose_name='Nom complet normalisé', db_index=True)),
                ('archive', models.CharField(max_length=255, default='', blank=True, verbose_name='Archive', db_index=True)),
                ('version', models.CharField(max_length=255, default='', blank=True, verbose_name='Version', db_index=True)),
                ('filename', models.CharField(max_length=255, default='', db_index=True, help_text='généré automatiquement à la création', blank=True, verbose_name='nom de fichier')),
                ('uuid', models.CharField(max_length=40, help_text='Unique identifier, automatically generated on first save', blank=True, verbose_name='UUID', db_index=True)),
                ('md5', models.CharField(max_length=120, default='', db_index=True, help_text='généré automatiquement à la création', blank=True, verbose_name='somme MD5')),
                ('sha1', models.CharField(max_length=120, default='', db_index=True, help_text='généré automatiquement à la création', blank=True, verbose_name='somme SHA1')),
                ('sha256', models.CharField(max_length=120, default='', db_index=True, help_text='généré automatiquement à la création', blank=True, verbose_name='somme SHA256')),
                ('filesize', models.IntegerField(default=0, blank=True, verbose_name='taille', db_index=True, help_text='généré automatiquement à la création')),
                ('extension', models.CharField(max_length=20, default='', db_index=True, help_text='généré automatiquement à la création', blank=True, verbose_name='extension')),
                ('mimetype', models.CharField(max_length=40, default='', db_index=True, help_text='Guessed on creation', blank=True, verbose_name='MIME type')),
                ('archive_file', models.FileField(default='', upload_to='uploads', help_text='Any text, binary or archive file.', blank=True, verbose_name='Archive file', null=True)),
                ('archive_key', models.CharField(max_length=255, default='', blank=True, verbose_name='Original file', db_index=True)),
                ('uncompressed_key', models.CharField(max_length=255, default='', blank=True, verbose_name='Stored path', db_index=True)),
                ('extra_data', models.TextField(default='', blank=True, verbose_name='Extra repo data')),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL, blank=True, verbose_name='Auteur', null=True)),
            ],
            options={
                'verbose_name_plural': 'files',
                'verbose_name': 'file',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ElementSignature',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('signature', models.TextField(default='', blank=True, verbose_name='signature')),
                ('method', models.CharField(max_length=10, verbose_name='méthode de signature', db_index=True, choices=[('gpg', 'GnuPG'), ('openssl', 'OpenSSL/x509')])),
                ('creation', models.DateTimeField(db_index=True, auto_now_add=True, verbose_name='Date de création')),
                ('element', models.ForeignKey(default=0, to='repository.Element', verbose_name='Élément')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Repository',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('name', models.CharField(max_length=100, verbose_name='Nom', db_index=True)),
                ('slug', models.SlugField(max_length=100, verbose_name='Nom raccourci')),
                ('creation', models.DateTimeField(db_index=True, auto_now_add=True, verbose_name='Date de création')),
                ('modification', models.DateTimeField(auto_now=True, db_index=True, verbose_name='Date de modification')),
                ('archive_type', models.CharField(max_length=100, verbose_name='Type de dépôt', db_index=True, choices=[('aptitude', 'APT repository for Linux .deb packages'), ('maven3', 'Maven repository for Java packages'), ('pypy', 'Pypi repository for Python packages')])),
                ('is_public', models.BooleanField(default=True, verbose_name='Dépôt accessible publiquement ?', db_index=True)),
                ('on_index', models.BooleanField(default=True, verbose_name='Display on public index?', db_index=True)),
                ('is_private', models.BooleanField(default=False, verbose_name='Authentification requise en lecture ?', db_index=True)),
                ('admin_group', models.ManyToManyField(blank=True, verbose_name="Groupes d'administration", db_index=True, to='auth.Group', related_name='repository_admin')),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL, blank=True, verbose_name='Auteur', null=True)),
                ('reader_group', models.ManyToManyField(blank=True, verbose_name='Groupes ayant accès en lecture', db_index=True, to='auth.Group', related_name='repository_reader')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='element',
            name='repository',
            field=models.ForeignKey(to='repository.Repository', verbose_name='Dépôt'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='element',
            name='states',
            field=models.ManyToManyField(to='repository.ArchiveState', verbose_name='États possibles', db_index=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='archivestate',
            name='repository',
            field=models.ForeignKey(to='repository.Repository', verbose_name='Dépôt'),
            preserve_default=True,
        ),
    ]
