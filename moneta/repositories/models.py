# coding=utf-8
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from moneta.repository.models import ArchiveState, Repository, BaseModel

__author__ = 'flanker'


class Image(BaseModel):
    states = models.ManyToManyField(ArchiveState, verbose_name=_('Archive states'), db_index=True)
    repository = models.ForeignKey(Repository, verbose_name=_('Repository'), db_index=True)
    tag = models.CharField(_('Tag'), db_index=True, max_length=255, blank=True, null=True, default=None)
    digest = models.CharField(_('Digest'), db_index=True, max_length=255, blank=True, null=True, default=None)
    manifest = models.TextField(_('Manifest content'), blank=True, default='')

    class Meta:
        verbose_name = _('Docker image')
        verbose_name_plural = _('Docker image')


class LayerBlob(BaseModel):
    creation = models.DateTimeField(_('Creation date'), db_index=True, auto_now_add=True)
    modification = models.DateTimeField(_('Modification date'), db_index=True, auto_now=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('Author'), db_index=True, blank=True, null=True)
    image = models.ForeignKey(Image, db_index=True, blank=True, null=True, default=None)
    repository = models.ForeignKey(Repository, verbose_name=_('Repository'), db_index=True)
    uuid = models.CharField(_('UUID'), db_index=True, max_length=40, blank=True, help_text=_('Unique identifier'))
    md5 = models.CharField(_('MD5 sum'), max_length=120, blank=True, db_index=True, default='',
                           help_text=_('Automatically generated on creation'))
    sha1 = models.CharField(_('SHA1 sum'), max_length=120, blank=True, db_index=True, default='',
                            help_text=_('Automatically generated on creation'))
    sha256 = models.CharField(_('SHA256 sum'), max_length=120, blank=True, db_index=True, default='',
                              help_text=_('Automatically generated on creation'))
    filesize = models.IntegerField(_('File size'), default=0, blank=True, db_index=True,
                                   help_text=_('Automatically computed on upload'))
    archive_key = models.CharField(_('Layer key'), blank=True, max_length=255, db_index=True, default='')

    class Meta:
        verbose_name = _('Docker image layer')
        verbose_name_plural = _('Docker image layer')
