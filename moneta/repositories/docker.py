# -*- coding: utf-8 -*-
import hashlib
import json
import re
import uuid

import io
from django.conf import settings
from django.conf.urls import url
from django.db.models import Q
from django.http import HttpResponse
from django.http import JsonResponse
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from moneta.repositories.base import RepositoryModel
from moneta.repositories.models import Image, LayerBlob
from moneta.repository.models import ArchiveState, storage
from moneta.repository.models import Repository
from moneta.templatetags.moneta import moneta_url

__author__ = 'Matthieu Gallet'


class Docker(RepositoryModel):
    verbose_name = _('Docker Repository')
    storage_uid = 'a97072de-0000-0000-0000-%012d'
    archive_type = 'docker'
    index_html = ''

    def url_list(self):
        """
        Return a list of URL patterns specific to this repository
        :return: a patterns as expected by django
        """
        return []

    def public_url_list(self):
        np = '(?P<name>[a-z]+)'
        return [url(r"^(?P<rid>\d+)/$", self.wrap_view('index'), name="index"),
                url(r'^(?P<rid>\d+)/v2/$', self.wrap_view('api_endpoint'), name='api_endpoint'),
                url(r'^(?P<rid>\d+)/v2/%s/blobs/uploads/$' % np, self.wrap_view('blob_uploads', csrf_exempt=True),
                    name='blob_uploads'),
                url(r'^(?P<rid>\d+)/v2/%s/blobs/uploads/(?P<layer_uid>[\da-f]{36})$' % np,
                    self.wrap_view('blob_add_upload', csrf_exempt=True), name='blob_add_upload'),
                url(r'^(?P<rid>\d+)/v2/%s/blobs/(?P<digest_method>md5|sha1|sha256):(?P<digest>[\da-f]+)$' % np,
                    self.wrap_view('blob', csrf_exempt=True), name='blob'),
                url(r'^(?P<rid>\d+)/v2/%s/manifests/(?P<reference>.+)$' % np,
                    self.wrap_view('manifests', csrf_exempt=True), name='manifests'),
                url(r'^(?P<rid>\d+)/v2/_catalog$', self.wrap_view('catalog', csrf_exempt=True), name='catalog'),
                url(r'^(?P<rid>\d+)/v2/%s/tags/list$' % np,
                    self.wrap_view('tags', csrf_exempt=True), name='tags'),
                ]

    def index(self, request, rid):
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.archive_type)
        states = [state for state in ArchiveState.objects.filter(repository=repo).order_by('name')]
        tab_infos = [(states, ArchiveState(name=_('All states'), slug='all-states')), ]
        tab_infos += [([state], state) for state in states]

        template_values = {'repo': repo, 'states': states, 'upload_allowed': repo.upload_allowed(request),
                           'index_url': reverse(moneta_url(repo, 'index'), kwargs={'rid': repo.id, }),
                           'tab_infos': tab_infos, 'admin_allowed': repo.admin_allowed(request), }
        return TemplateResponse(request, self.index_html, template_values)

    def api_endpoint(self, request, rid):
        """
        GET /v2/

        204 No Content
        """
        if Repository.reader_queryset(request).filter(id=rid, archive_type=self.archive_type).first() is None:
            return HttpResponse(status=404)
        response = HttpResponse(status=204)
        response['Docker-Distribution-API-Version'] = 'registry/2.0'
        return response

    def blob_uploads(self, request, rid, name):
        """
        POST /v2/<name>/blobs/uploads/
        202 Accepted
        Location: /v2/<name>/blobs/uploads/<uuid>
        Range: bytes=0-<offset>
        Content-Length: 0
        Docker-Upload-UUID: <uuid>

        """
        repo = Repository.upload_queryset(request).filter(id=rid, archive_type=self.archive_type).first()
        if repo is None:
            return HttpResponse(status=404)
        if request.method == 'POST':
            slug = slugify(name)
            layer = LayerBlob(name=name, author=request.user, uuid=str(uuid.uuid4()), repository=repo)
            layer.archive_key = storage(settings.STORAGE_ARCHIVE).store_descriptor(layer.uuid, slug, io.BytesIO())
            layer.save()
            response = HttpResponse(status=202)
            response['Location'] = reverse('docker:blob_add_upload',
                                           kwargs={'rid': repo.id, 'name': name, 'layer_uid': layer.uuid})
            response['Range'] = 'bytes=0-0'
            response['Content-Length'] = '0'
            response['Docker-Upload-UUID'] = layer.uuid
            return response
        return HttpResponse(status=405)

    def blob_add_upload(self, request, rid, name, layer_uid):
        """
        DELETE /v2/<name>/blobs/uploads/<uuid>
        202 Accepted
        Content-Length: None

        GET /v2/<name>/blobs/uploads/<uuid>
        204 No Content
        Location: /v2/<name>/blobs/uploads/<uuid>
        Range: bytes=0-<offset>
        Docker-Upload-UUID: <uuid>

        PATCH /v2/<name>/blobs/uploads/<uuid>
        Content-Length: <size of chunk>
        Content-Range: <start of range>-<end of range>
        Content-Type: application/octet-stream
        <Layer Chunk Binary Data>
        202 Accepted
        Location: /v2/<name>/blobs/uploads/<uuid>
        Range: bytes=0-<offset>
        Content-Length: 0
        Docker-Upload-UUID: <uuid>

        PUT /v2/<name>/blobs/uploads/<uuid>?digest=<digest>
        Content-Length: <size of layer>
        Content-Type: application/octet-stream
        <Layer Binary Data>
        201 Created
        Location: /v2/<name>/blobs/<digest>
        Content-Length: 0
        Docker-Content-Digest: <digest>

        PUT /v2/<name>/blob/uploads/<uuid>?digest=<digest>
        Content-Length: <size of chunk>
        Content-Range: <start of range>-<end of range>
        Content-Type: application/octet-stream
        <Last Layer Chunk Binary Data>
        201 Created
        Location: /v2/<name>/blobs/<digest>
        Content-Length: 0
        Docker-Content-Digest: <digest>


        """
        repo = Repository.upload_queryset(request).filter(id=rid, archive_type=self.archive_type).first()
        if repo is None:
            return HttpResponse(status=404)
        layer = LayerBlob.objects.filter(name=name, uuid=layer_uid, repository=repo).first()
        if layer is None:
            return HttpResponse(status=404)
        if request.method == 'GET':
            if layer.sha256:
                response = HttpResponse(status=204)
                response['Location'] = reverse('docker:blob_add_upload',
                                               kwargs={'rid': repo.id, 'name': name, 'layer_uid': layer.uuid})
                response['Range'] = 'bytes=0-%d' % layer.filesize
                response['Docker-Upload-UUID'] = layer.uuid
                return response
            return HttpResponse(status=404)
        elif request.method == 'DELETE':
            layer.delete()
            response = HttpResponse(status=202)
            response['Content-Length'] = ''
            return response
        elif request.method == 'PATCH':
            matcher_length = re.match('^(\d+)$', request.META.get('Content-Length', ''))
            if not matcher_length:
                return HttpResponse(status=406, content='Invalid Content-Length header')
            matcher_range = re.match('^(\d+)-(\d+)$', request.META.get('Content-Range', ''))
            if not matcher_range:
                return HttpResponse(status=406, content='Invalid Content-Range header')
            length, start, end = int(matcher_length.group(1)), int(matcher_range.group(1)), int(matcher_range.group(2))
            if start != layer.filesize:
                return HttpResponse(status=406, content='Invalid start range (expected: %d)' % layer.filesize)
            fd = storage(settings.STORAGE_ARCHIVE).get_file(layer.archive_key, mode='ab')
            added_size = 0
            for data in iter(lambda: request.read(4096), b''):
                fd.write(data)
                layer.filesize += len(data)
                added_size += len(data)
            layer.save()
            fd.close()
            response = HttpResponse(status=202)
            response['Location'] = reverse('docker:blob_add_upload',
                                           kwargs={'rid': repo.id, 'name': name, 'layer_uid': layer.uuid})
            response['Range'] = 'bytes=0-%d' % layer.filesize
            response['Content-Length'] = '0'
            response['Docker-Upload-UUID'] = layer.uuid
            return response
        elif request.method == 'PUT':
            expected_digest_method, sep, expected_digest_value = request.GET.get('digest', '')
            if expected_digest_method not in ('md5', 'sha1', 'sha256'):
                return HttpResponse(status=406, content='Invalid digest method (must be one of sha1, md5, or sha256)')
            matcher_length = re.match('^(\d+)$', request.META.get('Content-Length', ''))
            if not matcher_length:
                return HttpResponse(status=406, content='Invalid Content-Length header')
            matcher_range = re.match('^(\d+)-(\d+)$', request.META.get('Content-Range', ''))
            if matcher_range:
                length, start, end = int(matcher_length.group(1)), int(matcher_range.group(1)), \
                                     int(matcher_range.group(2))
                if start != layer.filesize:
                    return HttpResponse(status=406, content='Invalid start range (expected: %d)' % layer.filesize)
                fd = storage(settings.STORAGE_ARCHIVE).get_file(layer.archive_key, mode='ab')
            else:
                fd = storage(settings.STORAGE_ARCHIVE).get_file(layer.archive_key, mode='wb')
            added_size = 0
            for data in iter(lambda: request.read(4096), b''):
                fd.write(data)
                layer.filesize += len(data)
                added_size += len(data)
            fd.close()
            fd = storage(settings.STORAGE_ARCHIVE).get_file(layer.archive_key, mode='rb')
            md5, sha1, sha256 = hashlib.md5(), hashlib.sha1(), hashlib.sha256()
            for data in iter(lambda: fd.read(4096), b''):
                md5.update(data)
                sha1.update(data)
                sha256.update(data)
            layer.md5 = md5.hexdigest()
            layer.sha1 = sha1.hexdigest()
            layer.sha256 = sha256.hexdigest()
            actual_digest_value = {'md5': layer.md5, 'sha1': layer.sha1, 'sha256': layer.sha256}[expected_digest_method]
            if expected_digest_value != actual_digest_value:
                return HttpResponse(status=406, content='Invalid digest (%s instead of %s)' %
                                                        (actual_digest_value, expected_digest_value))
            layer.save()
            # Docker-Content-Digest: <digest>
            response = HttpResponse(status=201)
            response['Location'] = reverse('docker:blob',
                                           kwargs={'rid': repo.id, 'name': name, 'digest_method': 'sha256',
                                                   'digest': layer.sha256})
            response['Content-Length'] = '0'
            response['Docker-Content-Digest'] = 'sha256:%s' % layer.sha256
            return response
        return HttpResponse(status=405)

    def blob(self, request, rid, name, digest_method, digest):
        """
    HEAD /v2/<name>/blobs/<digest>
        200 OK
        Content-Length: <length of blob>
        Docker-Content-Digest: <digest>
    GET /v2/<name>/blobs/<digest>
        200 OK
        Content-Length: <length of blob>
        Docker-Content-Digest: <digest>
    DELETE /v2/<name>/blobs/<digest>
        202 Accepted
        Content-Length: None

        """
        if request.method == 'HEAD':
            repo = Repository.reader_queryset(request).filter(id=rid, archive_type=self.archive_type).first()
            if repo is None:
                return HttpResponse(status=404)
            layer = LayerBlob.objects.filter(repository=repo, name=name, **{digest_method: digest}).first()
            if layer is None:
                return HttpResponse(status=404)
            response = HttpResponse(status=200, content_type='application/octet-stream')
            response['Content-Length'] = '%d' % layer.filesize
            response['Docker-Content-Digest'] = 'sha256:%s' % layer.sha256
            return response
        elif request.method == 'GET':
            repo = Repository.reader_queryset(request).filter(id=rid, archive_type=self.archive_type).first()
            if repo is None:
                return HttpResponse(status=404)
            layer = LayerBlob.objects.filter(repository=repo, name=name, **{digest_method: digest}).first()
            if layer is None:
                return HttpResponse(status=404)
            fd = storage(settings.STORAGE_ARCHIVE).get_file(layer.archive_key, mode='rb')
            response = StreamingHttpResponse(fd, status=200, content_type='application/octet-stream')
            response['Content-Length'] = '%d' % layer.filesize
            response['Docker-Content-Digest'] = 'sha256:%s' % layer.sha256
            return response
        elif request.method == 'DELETE':
            repo = Repository.upload_queryset(request).filter(id=rid, archive_type=self.archive_type).first()
            if repo is None:
                return HttpResponse(status=404)
            layer = LayerBlob.objects.filter(repository=repo, name=name, image=None, **{digest_method: digest}).first()
            if layer is None:
                return HttpResponse(status=404)
            layer.delete()
            response = HttpResponse(status=202)
            response['Content-Length'] = ''
            return response
        return HttpResponse(status=405)

    def manifests(self, request, rid, name, reference):
        """
        GET /v2/<name>/manifests/<reference>
            Content-Type: <manifest media type>

        PUT /v2/<name>/manifests/<reference>
            Content-Type: <manifest media type>
            {
               "name": <name>,
               "tag": <tag>,
               "fsLayers": [
                  {
                     "blobSum": <digest>
                  },
                  ...
                ]
               ],
               "history": <v1 images>,
               "signature": <JWS>,
               ...
            }

        DELETE /v2/<name>/manifests/<reference>
            202 Accepted
            Content-Length: None
        """
        if request.method == 'PUT':
            repo = Repository.upload_queryset(request).filter(id=rid, archive_type=self.archive_type).first()
            if repo is None:
                return HttpResponse(status=404)
            try:
                manifest_str = request.body.read().decode('utf-8')
                manifest_content = json.loads(manifest_str)
            except ValueError:
                return HttpResponse(status=406, content='Invalid manifest')
            # request.META.get('Content-Type', '')
            tag = manifest_content.get('tag')
            available_layers = {}
            for layer in LayerBlob.objects.filter(image=None, repository=repo):
                available_layers[layer.md5] = layer
                available_layers[layer.sha1] = layer
                available_layers[layer.sha256] = layer
            errors = []
            layer_ids = []
            for layer_data in manifest_content['fsLayers']:
                method, sep, value = layer_data['blobSum'].partition(':')
                if value not in available_layers:
                    errors.append({'code': 'BLOB_UNKNOWN', 'message': 'blob unknown to registry',
                                   'detail': {'digest': layer_data['blobSum']}})
                else:
                    layer_ids.append(available_layers[value].id)
            image = Image(name=name, tag=tag, repository=repo, manifest=manifest_str)
            image.save()
            LayerBlob.objects.filter(id__in=layer_ids, repository=repo).update(image=image)
            return HttpResponse(status=201)
        elif request.method == 'GET':
            repo = Repository.reader_queryset(request).filter(id=rid, archive_type=self.archive_type).first()
            if repo is None:
                return HttpResponse(status=404)
            image = Image.objects.filter(Q(tag=reference) | Q(digest=reference), name=name, repository=repo).first()
            if image is None:
                return HttpResponse(status=404)
            manifest_content = json.loads(image.manifest)
            media_type = manifest_content.get('mediaType', 'application/vnd.docker.distribution.manifest.v1+prettyjws')
            return HttpResponse(image.manifest, status=200, content_type=media_type)
        elif request.method == 'DELETE':
            repo = Repository.admin_queryset(request).filter(id=rid, archive_type=self.archive_type).first()
            if repo is None:
                return HttpResponse(status=404)
            image = Image.objects.filter(digest=reference, name=name, repository=repo).first()
            if image is None:
                return HttpResponse(status=404)
            for layer in LayerBlob.objects.filter(image=image, repository=repo):
                layer.delete()
            image.delete()
            response = HttpResponse(status=202)
            response['Content-Length'] = ''
            return response
        return HttpResponse(status=405)

    def catalog(self, request, rid):
        """
        GET /v2/_catalog
            200 OK
            Content-Type: application/json
            Link: <<url>?n=<n from the request>&last=<last repository in response>>; rel="next"
            {
              "repositories": [
                <name>,
                ...
              ]
            }
        """
        repo = Repository.reader_queryset(request).filter(id=rid, archive_type=self.archive_type).first()
        if repo is None:
            return HttpResponse(status=404)
        base_query = Image.objects.filter(repository=repo).order_by('name')
        query = self.format_query(request, base_query)
        names = list({obj.name for obj in query})
        names.sort()
        result = {'repositories': names}
        return JsonResponse(result)

    def tags(self, request, rid, name):
        """
        GET /v2/<name>/tags/list
            200 OK
            Content-Type: application/json
            Link: <<url>?n=<n from the request>&last=<last tag value from previous response>>; rel="next"
            {
              "name": <name>,
              "tags": [
                <tag>,
                ...
              ]
            }
        """
        repo = Repository.reader_queryset(request).filter(id=rid, archive_type=self.archive_type).first()
        if repo is None:
            return HttpResponse(status=404)
        base_query = Image.objects.filter(repository=repo, name=name)
        query = self.format_query(request, base_query)
        tags = list({obj.tag for obj in query})
        tags.sort()
        result = {'tags': tags}
        return JsonResponse(result)

    @staticmethod
    def format_query(request, base_query):
        matcher = re.match('^\d+$', request.GET.get('n', ''))
        start = 0
        if matcher:
            start = int(request.GET['n'])
        matcher = re.match('^\d+$', request.GET.get('last', ''))
        if matcher:
            last = int(request.GET['last'])
            return base_query[start:last + 1]
        else:
            return base_query[start:]
