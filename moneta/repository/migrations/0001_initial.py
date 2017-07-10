from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArchiveState',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=100, verbose_name='Nom')),
                ('slug', models.SlugField(max_length=100, verbose_name='Nom raccourci')),
                ('creation', models.DateTimeField(db_index=True, auto_now_add=True, verbose_name='Date de création')),
                ('modification', models.DateTimeField(db_index=True, auto_now=True, verbose_name='Date de modification')),
                ('author', models.ForeignKey(blank=True, null=True, verbose_name='Auteur', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Element',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=100, verbose_name='Nom')),
                ('slug', models.SlugField(max_length=100, verbose_name='Nom raccourci')),
                ('creation', models.DateTimeField(db_index=True, auto_now_add=True, verbose_name='Date de création')),
                ('modification', models.DateTimeField(db_index=True, auto_now=True, verbose_name='Date de modification')),
                ('official_link', models.URLField(max_length=255, blank=True, verbose_name='URL pour la page web')),
                ('short_description', models.CharField(max_length=500, blank=True, verbose_name='Description courte')),
                ('long_description', models.TextField(blank=True, verbose_name='Description longue')),
                ('full_name', models.CharField(db_index=True, max_length=255, blank=True, verbose_name='Nom complet')),
                ('full_name_normalized', models.CharField(db_index=True, max_length=255, blank=True, help_text='Nom complet, sans caractères spéciaux', verbose_name='Nom complet normalisé')),
                ('archive', models.CharField(db_index=True, max_length=255, blank=True, default='', verbose_name='Archive')),
                ('version', models.CharField(db_index=True, max_length=255, blank=True, default='', verbose_name='Version')),
                ('filename', models.CharField(max_length=255, blank=True, verbose_name='nom de fichier', db_index=True, default='', help_text='généré automatiquement à la création')),
                ('uuid', models.CharField(db_index=True, max_length=40, blank=True, help_text='Unique identifier, automatically generated on first save', verbose_name='UUID')),
                ('md5', models.CharField(max_length=120, blank=True, verbose_name='somme MD5', db_index=True, default='', help_text='généré automatiquement à la création')),
                ('sha1', models.CharField(max_length=120, blank=True, verbose_name='somme SHA1', db_index=True, default='', help_text='généré automatiquement à la création')),
                ('sha256', models.CharField(max_length=120, blank=True, verbose_name='somme SHA256', db_index=True, default='', help_text='généré automatiquement à la création')),
                ('filesize', models.IntegerField(db_index=True, blank=True, default=0, help_text='généré automatiquement à la création', verbose_name='taille')),
                ('extension', models.CharField(max_length=20, blank=True, verbose_name='extension', db_index=True, default='', help_text='généré automatiquement à la création')),
                ('mimetype', models.CharField(max_length=40, blank=True, verbose_name='MIME type', db_index=True, default='', help_text='Guessed on creation')),
                ('archive_file', models.FileField(blank=True, upload_to='uploads', null=True, verbose_name='Archive file', default='', help_text='Any text, binary or archive file.')),
                ('archive_key', models.CharField(db_index=True, max_length=255, blank=True, default='', verbose_name='Original file')),
                ('uncompressed_key', models.CharField(db_index=True, max_length=255, blank=True, default='', verbose_name='Stored path')),
                ('extra_data', models.TextField(blank=True, default='', verbose_name='Extra repo data')),
                ('author', models.ForeignKey(blank=True, null=True, verbose_name='Auteur', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'files',
                'verbose_name': 'file',
            },
        ),
        migrations.CreateModel(
            name='ElementSignature',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('signature', models.TextField(blank=True, default='', verbose_name='signature')),
                ('method', models.CharField(db_index=True, max_length=10, choices=[('gpg', 'GnuPG'), ('openssl', 'OpenSSL/x509')], verbose_name='méthode de signature')),
                ('creation', models.DateTimeField(db_index=True, auto_now_add=True, verbose_name='Date de création')),
                ('element', models.ForeignKey(verbose_name='Élément', default=0, to='repository.Element')),
            ],
        ),
        migrations.CreateModel(
            name='Repository',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=100, verbose_name='Nom')),
                ('slug', models.SlugField(max_length=100, verbose_name='Nom raccourci')),
                ('creation', models.DateTimeField(db_index=True, auto_now_add=True, verbose_name='Date de création')),
                ('modification', models.DateTimeField(db_index=True, auto_now=True, verbose_name='Date de modification')),
                ('archive_type', models.CharField(db_index=True, max_length=100, verbose_name='Type de dépôt')),
                ('on_index', models.BooleanField(db_index=True, default=True, verbose_name='Display on public index?')),
                ('is_private', models.BooleanField(db_index=True, default=False, verbose_name='Authentification requise en lecture ?')),
                ('admin_group', models.ManyToManyField(db_index=True, related_name='repository_admin', blank=True, to='auth.Group', verbose_name="Groupes d'administration")),
                ('author', models.ForeignKey(blank=True, null=True, verbose_name='Auteur', to=settings.AUTH_USER_MODEL)),
                ('reader_group', models.ManyToManyField(db_index=True, related_name='repository_reader', blank=True, to='auth.Group', verbose_name='Groupes ayant accès en lecture')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='element',
            name='repository',
            field=models.ForeignKey(to='repository.Repository', verbose_name='Dépôt'),
        ),
        migrations.AddField(
            model_name='element',
            name='states',
            field=models.ManyToManyField(db_index=True, to='repository.ArchiveState', verbose_name='États possibles'),
        ),
        migrations.AddField(
            model_name='archivestate',
            name='repository',
            field=models.ForeignKey(to='repository.Repository', verbose_name='Dépôt'),
        ),
    ]
