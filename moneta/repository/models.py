#coding=utf-8
import logging
import multiprocessing
import os
import uuid

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils.text import slugify
from django.utils.translation import ugettext as _, ugettext

from moneta.core.exceptions import InvalidRepositoryException
from moneta.core.utils import normalize_str, remove, import_path

__author__ = 'flanker'


from django.db import models
logger = logging.getLogger('moneta.files')


MUTEX = multiprocessing.Lock()
ARCHIVE_FILTER_CALLABLES = None
STORAGES = {}


def storage(name):
    global STORAGES, MUTEX
    if name not in STORAGES:
        MUTEX.acquire()
        kwargs = settings.STORAGES.get(name, settings.STORAGES['default'])
        cls = import_path(kwargs['ENGINE'])
        STORAGES[name] = cls(**kwargs)
        MUTEX.release()
    return STORAGES[name]


def archive_filters():
    """
    Check if archive filters set in settings are loaded. If not, load them.

    :return: a list of callable to call on new archives files.
    """
    global ARCHIVE_FILTER_CALLABLES, MUTEX
    MUTEX.acquire()
    if ARCHIVE_FILTER_CALLABLES is None:
        # noinspection PyPep8Naming
        ARCHIVE_FILTER_CALLABLES = []
        for middleware_path in settings.ARCHIVE_FILTERS:
            ARCHIVE_FILTER_CALLABLES.append(import_path(middleware_path))
    MUTEX.release()
    return ARCHIVE_FILTER_CALLABLES


class BaseModel(models.Model):
    name = models.CharField(_('Name'), max_length=100, blank=False, db_index=True)
    slug = models.SlugField(_('Slug'), max_length=100, blank=False, db_index=True)
    creation = models.DateTimeField(_('Creation date'), db_index=True, auto_now_add=True)
    modification = models.DateTimeField(_('Modification date'), db_index=True, auto_now=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('Author'), db_index=True, blank=True, null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class RepositoryModelsClasses(object):
    _models = None

    @classmethod
    def get_model(cls, cls_name):
        return cls.get_models()[cls_name]

    @classmethod
    def get_models(cls):
        MUTEX.acquire()
        if cls._models is None:
            # noinspection PyPep8Naming
            cls._models = {}
            for mw_path in settings.REPOSITORY_CLASSES:
                modelcls = import_path(mw_path)()
                cls._models[modelcls.archive_type] = modelcls
        MUTEX.release()
        return cls._models

    def __iter__(self):
        for x, y in self.get_models().items():
            yield x, str(y)


class Repository(BaseModel):
    archive_type = models.CharField(_('Repository type'), choices=RepositoryModelsClasses(), db_index=True,
                                    max_length=100)
    on_index = models.BooleanField(_('Display on public index?'), db_index=True, default=True, blank=True)
    is_private = models.BooleanField(_('Should readers be authenticated?'), db_index=True, default=False, blank=True)
    admin_group = models.ManyToManyField(Group, verbose_name=_('Admin groups'), db_index=True, blank=True,
                                         related_name='repository_admin')
    reader_group = models.ManyToManyField(Group, verbose_name=_('Readers groups'), db_index=True, blank=True,
                                          related_name='repository_reader')

    def get_model(self):
        return RepositoryModelsClasses.get_model(self.archive_type)

    def get_absolute_url(self):
        return reverse('%s:index' % self.archive_type, kwargs={'rid': self.id})

    @staticmethod
    def index_queryset(request):
        user = request.user
        if user.is_anonymous():
            return Repository.reader_queryset(request).filter(on_index=True)
        return Repository.reader_queryset(request).filter(Q(on_index=True) | Q(author=user))

    @staticmethod
    def admin_queryset(request):
        user = request.user
        if user.is_anonymous():
            return Repository.objects.filter(author=None).distinct()
        return Repository.objects.filter(Q(admin_group=user.groups.all()) | Q(author=user)).distinct()

    @staticmethod
    def reader_queryset(request):
        user = request.user
        if user.is_anonymous():
            return Repository.objects.filter(Q(is_private=False) | Q(author=None)).distinct()
        return Repository.objects.filter(Q(is_private=False) | Q(author=user) | Q(reader_group=user.groups.all())
                                         | Q(admin_group=user.groups.all())).distinct()

    def admin_allowed(self, request):
        user = request.user
        if user.is_anonymous():
            return self.author is None
        return self.author == user or \
            (not {x.id for x in user.groups.all()}.isdisjoint({x.id for x in self.admin_group.all()}))

    def reader_allowed(self, request):
        user = request.user
        if user.is_anonymous():
            return not self.is_private
        return not self.is_private or self.author == user or \
            (not {x.id for x in user.groups.all()}.isdisjoint({x.id for x in self.reader_group.all()})) or \
            (not {x.id for x in user.groups.all()}.isdisjoint({x.id for x in self.admin_group.all()}))


class ArchiveState(BaseModel):
    repository = models.ForeignKey(Repository, verbose_name=_('Repository'), db_index=True)


class Element(BaseModel):
    official_link = models.URLField(_('URL to the web page'), max_length=255, blank=True)
    short_description = models.CharField(_('Short description'), max_length=500, blank=True)
    long_description = models.TextField(_('Long description'), blank=True)
    states = models.ManyToManyField(ArchiveState, verbose_name=_('Archive states'), db_index=True)
    repository = models.ForeignKey(Repository, verbose_name=_('Repository'), db_index=True)
    full_name = models.CharField(_('Complete name'), max_length=255, blank=True, db_index=True)
    full_name_normalized = models.CharField(_('Normalized complete name'), max_length=255, blank=True, db_index=True,
                                            help_text=_("Complete name without special chars nor accents"))
    archive = models.CharField(_('Archive'), db_index=True, blank=True, default='', max_length=255)
    version = models.CharField(_('Version'), db_index=True, blank=True, default='', max_length=255)
    filename = models.CharField(_('filename'), max_length=255, blank=True, db_index=True, default='',
                                help_text=_('Automatically generated on creation'))
    uuid = models.CharField(_('UUID'), db_index=True, max_length=40, blank=True,
                            help_text=_('Unique identifier, automatically generated on first save'))
    md5 = models.CharField(_('MD5 sum'), max_length=120, blank=True, db_index=True, default='',
                           help_text=_('Automatically generated on creation'))
    sha1 = models.CharField(_('SHA1 sum'), max_length=120, blank=True, db_index=True, default='',
                            help_text=_('Automatically generated on creation'))
    sha256 = models.CharField(_('SHA256 sum'), max_length=120, blank=True, db_index=True, default='',
                              help_text=_('Automatically generated on creation'))
    filesize = models.IntegerField(_('File size'), default=0, blank=True, db_index=True,
                                   help_text=_('Automatically generated on creation'))
    extension = models.CharField(_('File extension'), db_index=True, max_length=20, blank=True, default='',
                                 help_text=_('Automatically generated on creation'))
    mimetype = models.CharField(_('MIME type'), db_index=True, max_length=40, blank=True, default='',
                                help_text=_('Guessed on creation'))
    archive_file = models.FileField(_('Archive file'), blank=True, default='', null=True,
                                    upload_to=settings.UPLOAD_ROOT, help_text=_('Any text, binary or archive file.'))
    archive_key = models.CharField(_('Original file'), blank=True, max_length=255, db_index=True, default='')
    uncompressed_key = models.CharField(_('Stored path'), blank=True, max_length=255, db_index=True, default='')
    extra_data = models.TextField(_('Extra repo data'), blank=True, default='')

    class Meta:
        verbose_name = _('file')
        verbose_name_plural = _('files')

    @staticmethod
    def reader_queryset(request):
        return Element.objects.filter(repository__in=Repository.reader_queryset(request))

    def remove_file(self):
        if self.archive_key:
            storage(settings.STORAGE_ARCHIVE).delete(self.archive_key)
            self.archive_key = None
        if self.uncompressed_key:
            storage(settings.STORAGE_UNCOMPRESSED).delete(self.uncompressed_key)
            self.uncompressed_key = None

    def delete(self, using=None):
        self.remove_file()
        result = super().delete(using=using)
        return result

    def save(self, *args, **kwargs):
        """
        :param args:
        :param kwargs:
        :return:
        """
        if not self.uuid:
            self.uuid = str(uuid.uuid1())
        if (self.archive_file is not None) and self.archive_file.name:  # a new file is uploaded
            uploaded_file = self.archive_file
            # noinspection PyBroadException
            try:
                uploaded_file.open('rb')
                filename = os.path.basename(uploaded_file.name)
                self.set_file(uploaded_file.file, filename)
            except Exception:
                logger.error(ugettext('Unable to add the archive file'), exc_info=True)
            exceptions = []
            cls = self.repository.get_model()
            if not cls.is_file_valid(uploaded_file):
                exceptions.append(str(self.repository))
            else:
                cls.element(self)
            if len(exceptions) == 1:
                raise InvalidRepositoryException(
                    _('Repository %(repo)s is unable to handle this file.') % {'repo': exceptions[0], })
            elif len(exceptions) > 1:
                raise InvalidRepositoryException(
                    _('Repositories %(repo)s are unable to handle this file.') % {'repo': _(', ').join(exceptions), })
            self.archive_file = None
        self.full_name = _('%(name)s-%(version)s %(filename)s') % {'name': self.name, 'version': self.version,
                                                                   'filename': self.filename}
        self.full_name_normalized = normalize_str(self.full_name)
        super().save(*args, **kwargs)

    def set_file(self, obj_file, filename):
        temp_files = set()
        # noinspection PyBroadException
        try:
            self.remove_file()
            self.archive_key = storage(settings.STORAGE_ARCHIVE).store_descriptor(self.uuid, filename, obj_file)
            uncompressed_path = None
            for mw in archive_filters():
                obj_file.seek(0)
                u_path = mw(self, obj_file, filename, temp_files, uncompressed_path)
                if u_path is not None:
                    uncompressed_path = u_path
            if uncompressed_path is not None:  # there are extracted data to store
                self.uncompressed_key = storage(settings.STORAGE_UNCOMPRESSED).store(self.uuid, uncompressed_path)
        except Exception as e:
            logging.error(ugettext('Unable to add the archive file'), exc_info=True)
            raise e
        for f in temp_files:
            remove(f)

    def __str__(self):
        return self.full_name

    def get_absolute_url(self):
        return reverse('moneta.core.views.show_file', kwargs={'eid': self.id}, )

    def get_direct_link(self):
        return reverse('moneta.core.views.get_file', kwargs={'eid': self.id}, ) + '/' + self.filename


class ElementSignature(models.Model):
    GPG = 'gpg'
    OPENSSL = 'openssl'
    METHODS = ((GPG, _('GnuPG')), (OPENSSL, _('OpenSSL/x509')))
    element = models.ForeignKey(Element, verbose_name=_('Element'), db_index=True, default=0)
    signature = models.TextField(_('signature'), default='', blank=True)
    method = models.CharField(_('signature method'), choices=METHODS, db_index=True, max_length=10)
    creation = models.DateTimeField(_('Creation date'), db_index=True, auto_now_add=True)


# noinspection PyUnusedLocal
@receiver(pre_delete, sender=Element)
def delete_element(sender, instance=None, **kwargs):
    """


    :type sender: object
    :param sender:
    :param instance:
    :param kwargs:
    """
    if instance is not None and isinstance(instance, Element):
        instance.remove_file()
