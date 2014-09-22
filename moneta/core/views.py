# coding=utf-8
import base64
from distutils.version import LooseVersion
import hashlib
import mimetypes
import os
import tarfile
import tempfile
import zipfile

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.files.uploadedfile import UploadedFile
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.core.validators import RegexValidator
from django.db.models import Count
from django.http import HttpResponseRedirect, Http404, StreamingHttpResponse, HttpResponse, \
    HttpResponsePermanentRedirect
from django.utils.six import u
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_exempt
import gnupg
import time

from moneta.core.exceptions import InvalidRepositoryException
from moneta.core.utils import read_file_in_chunks
from moneta.repository.forms import RepositoryForm, DeleteRepositoryForm, SignatureForm
from moneta.repository.models import Repository, ArchiveState, Element, storage, ElementSignature


__author__ = u('flanker')

from django.contrib.sites.models import get_current_site
from django.contrib.syndication.views import add_domain
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _


def robots(request):
    current_site = get_current_site(request)
    base_url = add_domain(current_site.domain, '/', request.is_secure())[:-1]
    template_values = {'base_url': base_url}
    return render_to_response('core/robots.txt', template_values, RequestContext(request), content_type='text/plain')


def default(request):
    return HttpResponsePermanentRedirect(reverse('moneta.core.views.index'))


def public_check(request):
    messages.success(request, _('You can access to this page.'))
    return render_to_response('core/empty.html', RequestContext(request))


def private_check(request):
    if request.user.is_anonymous():
        messages.error(request, _('You are not authenticated.'))
    else:
        messages.success(request, _('You can access to this page and you are authenticated.'))
    return render_to_response('core/empty.html', RequestContext(request))


def check(request):
    s_h = settings.SECURE_PROXY_SSL_HEADER
    a_h = settings.AUTHENTICATION_HEADER
    # noinspection PyArgumentList
    gpg = gnupg.GPG(homedir=settings.GNUPG_HOME, binary=settings.GNUPG_PATH)
    gpg_valid = False
    for key in gpg.list_keys(False):
        if key['keyid'] == settings.GNUPG_KEYID:
            gpg_valid = True
    import moneta.core.defaults
    import moneta.core.settings as real_settings
    default_conf_path = moneta.core.defaults.__file__
    if default_conf_path.endswith('.pyc'):
        default_conf_path = default_conf_path[:-1]

    template_values = {
        'media_root': settings.MEDIA_ROOT, 'media_url': settings.MEDIA_URL,
        'static_root': settings.STATIC_ROOT, 'static_url': settings.STATIC_URL,
        'debug': settings.DEBUG, 'use_x_forwared_host': settings.USE_X_FORWARDED_HOST,
        'secure_proxy_ssl_header_name': s_h[0][5:],
        'secure_proxy_ssl_header_value': s_h[1],
        'authentication_header': a_h,
        'has_authentication_header': request.META.get(a_h, '') == request.user.username,
        'has_secure_proxy_ssl_header': request.META.get(s_h[0], '') == s_h[1],
        'host': request.get_host().rpartition(':')[0],
        'has_allowed_host': request.get_host() in settings.ALLOWED_HOSTS,
        'gpg_valid': gpg_valid, 'gpg_available': gpg.list_keys(False),
        'conf_path': getattr(settings, 'CONF_PATH', None), 'conf_is_set': settings.CONF_IS_SET,
        'default_conf_path': default_conf_path, 'settings': real_settings.SETTINGS_VARIABLE
    }

    return render_to_response('core/help.html', template_values, RequestContext(request))


def index(request):
    repositories = Repository.index_queryset(request).annotate(package_count=Count('element'))
    if request.method == 'POST':
        form = RepositoryForm(request.POST)
        if request.user.is_anonymous():
            raise PermissionDenied()
        if form.is_valid():
            author = None if request.user.is_anonymous() else request.user
            repo = Repository(author=author, name=form.cleaned_data['name'], on_index=form.cleaned_data['on_index'],
                              archive_type=form.cleaned_data['archive_type'],
                              is_private=form.cleaned_data['is_private'])
            repo.save()
            for group in form.cleaned_data['admin_group']:
                repo.admin_group.add(group)
            for state in set(form.cleaned_data['states'].split()):
                ArchiveState(repository=repo, name=state, author=author).save()
            messages.info(request, _('Your new repository has been created.'))
            return HttpResponseRedirect(reverse('moneta.core.views.index'))
    else:
        form = RepositoryForm()
    # compute repos with admin rights
    admin_ids = {x.id for x in Repository.admin_queryset(request)}

    template_values = {'repositories': repositories, 'form': form, 'request': request,
                       'admin_ids': admin_ids}
    return render_to_response('core/index.html', template_values, RequestContext(request))


def modify_repository(request, rid):
    repo = get_object_or_404(Repository.admin_queryset(request), id=rid)
    author = None if request.user.is_anonymous() else request.user

    def repo_name_validator(value):
        if Repository.objects.exclude(id=rid).filter(slug=slugify(value)).count() > 0:
            raise ValidationError(_('This repository already exists.'))

    class RepositoryUpdateForm(forms.Form):
        name = forms.CharField(max_length=80, label=_('Repository name'), validators=[repo_name_validator])
        on_index = forms.BooleanField(label=_('Display on index for everybody?'), initial=True, required=False)
        is_private = forms.BooleanField(label=_('Must downloads be authenticated?'), initial=False, required=False)
        states = forms.CharField(label=_('Possible states'), initial='dev qualif prod',
                                 help_text=_('Please separate values by spaces'),
                                 validators=[RegexValidator('\w+(\s\w)*')])
        admin_group = forms.ModelMultipleChoiceField(Group.objects.all(), label=_('Groups allowed to upload'),
                                                     required=False)
        reader_group = forms.ModelMultipleChoiceField(Group.objects.all(),
                                                      help_text=_('Only if downloads are authenticated'),
                                                      label=_('Groups allowed to download packages'), required=False)

    if request.method == 'POST':
        form = RepositoryUpdateForm(request.POST)
        if form.is_valid():
            new_state_names = set(form.cleaned_data['states'].split())
            old_state_names = {x.name for x in repo.archivestate_set.all()}
            for name in new_state_names - old_state_names:  # new states
                ArchiveState(name=name, repository=repo, author=author).save()
            repo.name = form.cleaned_data['name']
            repo.on_index = form.cleaned_data['on_index']
            repo.is_private = form.cleaned_data['is_private']
            repo.save()
            repo.admin_group.clear()
            for group in form.cleaned_data['admin_group']:
                repo.admin_group.add(group)
            repo.reader_group.clear()
            for group in form.cleaned_data['reader_group']:
                repo.reader_group.add(group)
            removed_states = ArchiveState.objects.filter(name__in=old_state_names - new_state_names, repository=repo)
            Element.states.through.objects.filter(archivestate__in=removed_states).delete()
            removed_states.delete()
            messages.info(request, _('The repository %(repo)s has been modified.') % {'repo': repo.name})
            return HttpResponseRedirect(reverse('moneta.core.views.index'))
    else:
        form = RepositoryUpdateForm(initial={'name': repo.name, 'on_index': repo.on_index,
                                             'is_private': repo.is_private,
                                             'reader_group': list(repo.reader_group.all()),
                                             'states': ' '.join([x.name for x in repo.archivestate_set.all()]),
                                             'admin_group': list(repo.admin_group.all())})
    template_values = {'form': form, 'repo': repo, 'admin_allowed': repo.admin_allowed(request)}
    return render_to_response('core/modify_repo.html', template_values, RequestContext(request))


def search_package(request, rid):
    repo = get_object_or_404(Repository.reader_queryset(request), id=rid)

    class ElementSearchForm(forms.Form):
        search = forms.CharField(label=_('Search'), help_text=_('Type your search'), max_length=200, required=False)
        states = forms.ModelMultipleChoiceField(label=_('Selected states'), required=False,
                                                queryset=ArchiveState.objects.filter(repository=repo), )
        states.help_text = ''

    if request.GET.get('search') is not None:
        form = ElementSearchForm(request.GET)
    else:
        form = ElementSearchForm()
    query = Element.objects.filter(repository=repo)
    search_pattern = ''
    if form.is_valid():
        search_pattern = form.cleaned_data['search']
        if search_pattern:
            query = query.filter(full_name__icontains=search_pattern)
        if form.cleaned_data['states']:
            query = query.filter(states__in=form.cleaned_data['states']).distinct()

    paginator = Paginator(query.order_by('full_name'), 25)
    page = request.GET.get('page')

    try:
        elements = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        elements = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        elements = paginator.page(paginator.num_pages)

    template_values = {'elements': elements, 'repo': repo, 'pattern': search_pattern, 'form': form,
                       'admin_allowed': repo.admin_allowed(request)}
    return render_to_response('core/search_repo.html', template_values, RequestContext(request))


def delete_repository(request, rid):
    repo = get_object_or_404(Repository.admin_queryset(request), id=rid)
    if request.method == 'POST':
        form = DeleteRepositoryForm(request.POST)
        if form.is_valid():
            for element in Element.objects.filter(repository=repo):
                element.delete()
            repo.delete()
            messages.warning(request, _('The repository %(repo)s has been deleted.') % {'repo': repo.name})
            return HttpResponseRedirect(reverse('moneta.core.views.index'))
    else:
        form = DeleteRepositoryForm()
    template_values = {'form': form, 'repo': repo}
    return render_to_response('core/delete_repo.html', template_values, RequestContext(request))


def delete_element(request, rid, eid):
    repo = get_object_or_404(Repository.admin_queryset(request), id=rid)
    element = get_object_or_404(Element.objects.filter(repository=repo, id=eid))
    if request.method == 'POST':
        form = DeleteRepositoryForm(request.POST)
        if form.is_valid():
            element.delete()
            messages.warning(request, _('The package %(repo)s has been deleted.') % {'repo': element.full_name})
            return HttpResponseRedirect(reverse('moneta.core.views.index'))
    else:
        form = DeleteRepositoryForm()
    template_values = {'form': form, 'repo': repo, 'element': element}
    return render_to_response('core/delete_element.html', template_values, RequestContext(request))


def generic_add_element(request, repo, uploaded_file, state_names, archive=None, name=None, version=None):
    """ Generic upload (both form-based and raw POST-based methods)
    :param repo: Repository
    :param uploaded_file: UploadedFile
    :param state_names: iterable of ArchiveState.name
    :return: successfully added Element
    """
    sha256 = hashlib.sha256()
    data = uploaded_file.file.read(4096)
    while data:
        sha256.update(data)
        data = uploaded_file.file.read(4096)
    sha256_sum = sha256.hexdigest()
    uploaded_file.file.seek(0)
    if uploaded_file.name:
        filename = os.path.basename(uploaded_file.name)
        elements = list(Element.objects.filter(repository=repo, filename=filename)[0:1])
    elif name:
        name = os.path.basename(name)
        elements = list(Element.objects.filter(repository=repo, name=name)[0:1])
    else:
        elements = list(Element.objects.filter(repository=repo, sha256=sha256_sum)[0:1])
    if elements:
        element = elements[0]
    else:
        user = None if request.user.is_anonymous() else request.user
        element = Element(repository=repo, author=user)
    if archive:
        element.archive = archive
    if name:
        element.name = os.path.basename(name)
    if version:
        element.version = version
    element.archive_file = uploaded_file
    # form.cleaned_data['package'].file.name = form.cleaned_data['package'].name
    element.save()
    states = ArchiveState.objects.filter(repository=repo, slug__in=state_names)
    # remove previous versions
    Element.states.through.objects.exclude(element__version=element.version)\
        .filter(archivestate__in=states, element__archive=element.archive).delete()
    for state in states:
        element.states.add(state)
    return element


def add_element(request, rid):
    repo = get_object_or_404(Repository.admin_queryset(request), id=rid)

    class ElementForm(forms.Form):
        package = forms.FileField(label=_('Package'))
        states = forms.ModelMultipleChoiceField(repo.archivestate_set.all(), label=_('States'))

        def clean(self):
            data_ = super().clean()
            if 'package' in self.cleaned_data:
                if not repo.get_model().is_file_valid(self.cleaned_data['package']):
                    raise ValidationError(_('This repository is unable to handle this file.'))
            return data_

    if request.method == 'POST':
        form = ElementForm(request.POST, files=request.FILES)
        if form.is_valid():
            try:
                element = generic_add_element(request, repo, form.cleaned_data['package'],
                                              [x.name for x in form.cleaned_data['states']])
                messages.info(request, _('The package %(n)s has been successfully uploaded.') % {'n': element.filename})
            except InvalidRepositoryException:
                pass
            return HttpResponseRedirect(reverse('moneta.core.views.add_element', kwargs={'rid': rid}))
    else:
        form = ElementForm()
    template_values = {'form': form, 'repo': repo, 'admin_allowed': repo.admin_allowed(request)}
    return render_to_response('core/add_package.html', template_values, RequestContext(request))


@csrf_exempt
def add_element_signature(request, rid):
    if request.method != 'POST':
        return render_to_response('core/not_allowed.html', status=405)
    form = SignatureForm(request.GET)
    if not form.is_valid():
        return render_to_response('core/not_allowed.html', status=405)
    signature = base64.b64encode(request.read(16384))
    sha256 = form.cleaned_data['sha256']
    method = form.cleaned_data['method']
    user = None if request.user.is_anonymous() else request.user
    element = get_object_or_404(Element.reader_queryset(request), repository__id=rid, sha256=sha256, author=user)
    ElementSignature(element=element, signature=signature, method=method).save()
    return HttpResponse(_('This signature has been added to %(filename)s') % {'filename': element.filename})


@csrf_exempt
def add_element_post(request, rid):
    repo = get_object_or_404(Repository.admin_queryset(request), id=rid)
    if request.method != 'POST':
        return render_to_response('core/not_allowed.html', status=405)
    validators = [RegexValidator(r'[\w\.\-\(\)/]+')]

    class ElementForm(forms.Form):
        filename = forms.CharField(label=_('Package'), max_length=255, validators=validators)
        states = forms.MultipleChoiceField([(x.name, x.name) for x in repo.archivestate_set.all()], label=_('States'))
        name = forms.CharField(label=_('Name'), max_length=255, validators=validators, required=False)
        archive = forms.CharField(label=_('Archive'), max_length=255, validators=validators, required=False)
        version = forms.CharField(label=_('Version'), max_length=255, validators=validators, required=False)

    form = ElementForm(request.GET)
    if not form.is_valid():
        return render_to_response('core/not_allowed.html', status=405)

    tmp_file = tempfile.TemporaryFile(mode='w+b')
    c = False
    chunk = request.read(32768)
    while chunk:
        tmp_file.write(chunk)
        c = True
        chunk = request.read(32768)
    tmp_file.flush()
    tmp_file.seek(0)
    if not c:
        return HttpResponse(_('Empty file. You must POST a valid file.'), status=400)
    uploaded_file = UploadedFile(name=form.cleaned_data['filename'], file=tmp_file)
    try:
        element = generic_add_element(request, repo, uploaded_file, form.cleaned_data['states'],
                                      name=form.cleaned_data.get('name'), archive=form.cleaned_data.get('archive'),
                                      version=form.cleaned_data.get('version'), )
    except InvalidRepositoryException as e:
        return HttpResponse(str(e), status=400)
    finally:
        tmp_file.close()
    template_values = {'repo': repo, 'element': element}
    return HttpResponse(_('Package %(element)s successfully added to repository %(repo)s.') % template_values)


def show_file(request, eid):
    q = Element.reader_queryset(request).filter(id=eid).select_related()[0:1]
    elements = list(q)
    if len(elements) == 0:
        raise Http404
    element = elements[0]
    template_values = {'element': element, 'repo': element.repository,
                       'admin_allowed': element.repository.admin_allowed(request)}
    return render_to_response('core/show_package.html', template_values, RequestContext(request))


def get_checksum(request, eid, value):
    element = get_object_or_404(Element.reader_queryset(request), id=eid)
    value = getattr(element, value)
    return HttpResponse('%s ?%s\n' % (value, element.filename), content_type='text/plain')


def get_signature(request, eid, sid):
    element = get_object_or_404(Element.reader_queryset(request), id=eid)
    signature = get_object_or_404(ElementSignature, element=element, id=sid)
    value = base64.b64decode(signature.signature)
    mimetype = 'application/pgp-signature' if signature.method == signature.GPG else 'application/x509'
    return HttpResponse(value, content_type=mimetype)


def get_checksum_p(request, eid, value):
    return get_checksum(request, eid, value)


def get_file_p(request, eid, compression=None, path='', element=None, name=None):
    return get_file(request, eid, compression=compression, path=path, element=element, name=name)


def get_signature_p(request, eid, sid):
    return get_signature(request, eid, sid)


def get_file(request, eid, compression=None, path='', element=None, name=None):
    # noinspection PyUnusedLocal
    name = name
    if element is None:
        q = Element.reader_queryset(request).filter(id=eid).select_related()[0:1]
        elements = list(q)
        if len(elements) == 0:
            raise Http404
        element = elements[0]
    arc_storage, arc_key, arc_path = None, None, None
    filename = element.filename
    mimetype = 'application/octet-stream'
    if element.uncompressed_key and path:
        path = os.path.normpath(path)
        if path.startswith('../'):
            raise Http404
        filename = os.path.basename(path)
    elif element.uncompressed_key and compression is not None:
        arc_storage, arc_key, arc_path = storage(settings.STORAGE_UNCOMPRESSED), element.uncompressed_key, path
        filename = os.path.splitext(element.filename)[0]
    elif element.archive_key:
        if compression is not None:
            arc_storage, arc_key, arc_path = storage(settings.STORAGE_ARCHIVE), element.archive_key, ''
    else:
        raise Http404
    if arc_storage is not None:
        temp_file = tempfile.TemporaryFile(mode='w+b')
        comp_file = None
        ext = ''
        if compression == 'zip':
            mimetype = 'application/zip'
            ext = '.zip'
            comp_file = zipfile.ZipFile(temp_file, 'w', zipfile.ZIP_DEFLATED)
        elif compression == 'tgz':
            mimetype = 'application/x-tar'
            ext = '.tgz'
            comp_file = tarfile.open(None, 'w:gz', fileobj=temp_file)
            comp_file.write = comp_file.addfile
        elif compression == 'tbz':
            mimetype = 'application/x-tar'
            ext = '.tbz'
            comp_file = tarfile.open(None, 'w:bz2', fileobj=temp_file)
            comp_file.write = comp_file.addfile
        reldir = None
        for root, dirs, files in arc_storage.walk(arc_key, arc_path):
            if reldir is None:
                reldir = root
            for name in files:
                fullname = os.path.join(root, name)
                fileobj = arc_storage.get_file(arc_key, fullname)
                arcname = os.path.relpath(fullname, reldir)
                tarinfo = tarfile.TarInfo(arcname)
                tarinfo.size = arc_storage.get_size(arc_key, fullname)
                comp_file.write(tarinfo, fileobj)
        comp_file.close()
        temp_file.seek(0)
        fileobj = temp_file
        filename = os.path.basename(element.filename) + ext
    elif path:
        fileobj = storage(settings.STORAGE_UNCOMPRESSED).get_file(element.uncompressed_key, path)
        mimetype = mimetypes.guess_type(path)[0]
        if mimetype is None:
            mimetype = 'application/octet-stream'
    else:
        mimetype = element.mimetype
        fileobj = storage(settings.STORAGE_ARCHIVE).get_file(element.archive_key)

    response = StreamingHttpResponse(read_file_in_chunks(fileobj), content_type=mimetype)
    if mimetype[0:4] != 'text' and mimetype[0:5] != 'image':
        response['Content-Disposition'] = u'attachment; filename={0}'.format(filename)
    return response


def compare_states(request, rid):
    repo = get_object_or_404(Repository.reader_queryset(request), id=rid)
    states = ArchiveState.objects.filter(repository=repo)
    operators = {'<': lambda x, y: x < y, '<=': lambda x, y: x <= y, '==': lambda x, y: x == y,
                 '>=': lambda x, y: x >= y, '>': lambda x, y: x > y}

    class CompareForm(forms.Form):
        state_left = forms.ModelChoiceField(states, label=_('Left state'))
        operator = forms.ChoiceField([(x, x) for x in operators], label=_('Assert operator'))
        state_right = forms.ModelChoiceField(states, label=_('Right state'))

    template_values = {'repo': repo, 'admin_allowed': repo.admin_allowed(request)}
    if request.method == 'POST':
        form = CompareForm(request.POST)
        if form.is_valid():
            state_left = form.cleaned_data['state_left']
            state_right = form.cleaned_data['state_right']
            operator = operators[form.cleaned_data['operator']]
            left_elements = Element.objects.filter(repository=repo, states=state_left)
            right_elements = Element.objects.filter(repository=repo, states=state_right)
            left_dict = {}
            right_dict = {}
            for element in left_elements:
                left_dict.setdefault(element.archive, (LooseVersion(element.version), []))[1].append(element)
            for element in right_elements:
                right_dict.setdefault(element.archive, (LooseVersion(element.version), []))[1].append(element)
            only_left, only_right = {}, {}
            left_keys, right_keys = set(left_dict.keys()), set(right_dict.keys())
            for key in left_keys - right_keys:
                only_left[key] = left_dict[key]
            for key in right_keys - left_keys:
                only_right[key] = right_dict[key]
            invalid_values = []
            for key in left_keys.intersection(right_keys):
                if not operator(left_dict[key][0], right_dict[key][0]):
                    invalid_values.append((key, left_dict[key], right_dict[key]))
            invalid_values.sort(key=lambda x: x[0])
            template_values.update({'only_left': only_left, 'only_right': only_right, 'invalid_values': invalid_values,
                                    'state_left': state_left, 'state_right': state_right})
            template_values['all_valid'] = bool(not only_left and not only_right and not invalid_values)
    else:
        form = CompareForm()
    template_values['form'] = form
    return render_to_response('core/compare_states.html', template_values, RequestContext(request))


@csrf_exempt
def test_upload(request):
    start = time.time()
    size = 0.
    chunk = request.read(32768)
    while chunk:
        size += len(chunk)
        chunk = request.read(32768)
    end = time.time()
    ans = '%d s : %g o/s' % ((end - start), (size / (end - start)))
    return HttpResponse(ans.encode('utf-8'))