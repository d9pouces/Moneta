# -*- coding=utf-8 -*-
"""
Emulate a Maven3-compatible repository.


/$groupId[0]/../${groupId[n]/$artifactId/$version/$artifactId-$version.$extension
/$groupId[0]/../$groupId[n]/$artifactId/$version/$artifactId-$version-$classifier.$extension
/org/codehaus/plexus/plexus-container/0.15/
                     /plexus-container-0.15.jar
                     /plexus-container-0.15.jar.md5
                     /plexus-container-0.15.pom
                     /plexus-container-0.15.pom.md5
                     /plexus-container-0.15-javadoc.jar
                     /plexus-container-0.15-javadoc.jar.md5
                     /plexus-container-0.15-javasrc.jar
                     /plexus-container-0.15-javasrc.jar.md5

Maven3 variables:
    * $groupId = org.codehaus.plexus
    * $artifactId = plexus-container
    * $version = 0.15
    * $extension = jar
    * $classifier = javadoc, javasrc

Moneta mapping:
    * element.version maps to $version
    * element.archive maps to $groupId.$artifactId
    * element.name maps to $artifactId => built from element.archive
    * element.filename maps to $artifactId-$version-$classifier.$extension
    * element.full_name = element.filename

Command for uploading files:
curl --data-binary @$FILENAME http://[...]/\?filename=$FILENAME\&states=prod\&states=qualif\&archive=
$groupId.$artifactId\&version=$version

URLs to emulate:
    /$groupId[0]/../$groupId[n]/$artifactId/$version/(filename)$
    /$groupId[0]/../$groupId[n]/$artifactId/$version/(filename).md5$
    /$groupId[0]/../$groupId[n]/$artifactId/$version/(filename).sha1$
    /$groupId[0]/../$groupId[n]/$artifactId/$version/(filename).sha256$
"""
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _

from moneta.repositories.maven3 import Maven3
from moneta.repository.models import Repository, ArchiveState, Element
from moneta.templatetags.moneta import moneta_url

__author__ = 'flanker'


class FlatFile(Maven3):
    verbose_name = _('Simple repository for flat files')
    storage_uid = '91439a10-0000-0000-0000-%012d'
    archive_type = 'flat_files'

    def update_element(self, element):
        """
        Extract some informations from element to prepare the repository
        :param element: Element to add to the repository
        :return: Unicode string containing meta-data

        ar -x control.tar.gz
        tar -xf control.tar.gz control
        """
        if element.archive:
            element.name = element.archive.rpartition('.')[2]

    def finish_element(self, element: Element, states: list):
        """
        Called after the .save() operations, with all states associated to this new element.
        Remove previous versions from target states
        :param element: Element
        :param states: list of ArchiveState
        """
        # remove previous versions from the given states:
        # noinspection PyUnresolvedReferences
        Element.states.through.objects.exclude(element__version=element.version) \
            .filter(archivestate__in=states, element__archive=element.archive).delete()
        super().finish_element(element, states)

    def index(self, request, rid):
        repo = get_object_or_404(Repository.reader_queryset(request), id=rid, archive_type=self.archive_type)
        states = list(ArchiveState.objects.filter(repository=repo).order_by('name'))
        template_values = {'repo': repo, 'states': states, 'upload_allowed': repo.upload_allowed(request),
                           'admin_allowed': repo.admin_allowed(request), }
        state_infos = []
        template_values['state_slug'] = None
        viewname = moneta_url(repo, 'browse')
        url = reverse(viewname, kwargs={'rid': repo.id, 'repo_slug': repo.slug, })

        state_infos.append(('all-packages', url, _('All states'), states))
        for state in states:
            template_values['state_slug'] = state.slug
            url = reverse(viewname, kwargs={'rid': repo.id, 'repo_slug': repo.slug, 'state_slug': state.slug})
            state_infos.append((state.slug, url, state.name, [state]))
        template_values['state_infos'] = state_infos
        return TemplateResponse(request, 'repositories/flat_files/index.html', template_values)
