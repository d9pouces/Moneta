# coding=utf-8
from django import forms
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.text import slugify
from django.utils.translation import ugettext as _
import functools
from moneta.repository.models import Repository, ElementSignature

__author__ = 'flanker'


def repo_name_validator(value):
    if Repository.objects.filter(slug=slugify(value)).count() > 0:
        raise ValidationError(_('This repository already exists.'))


@functools.lru_cache()
def get_repository_form():
    from moneta.repositories.base import RepositoryModelsClasses

    class RepositoryForm(forms.Form):
        name = forms.CharField(max_length=80, label=_('Repository name'), validators=[repo_name_validator])
        archive_type = forms.ChoiceField(label=_('Type of archives'), choices=RepositoryModelsClasses())
        on_index = forms.BooleanField(label=_('Add on public index?'), initial=True, required=False)
        is_private = forms.BooleanField(label=_('Authentication required?'), initial=False, required=False, widget=forms.HiddenInput())
        states = forms.CharField(label=_('Possible states for archives'), initial='qualif prod',
                                 help_text=_('Please separate values by spaces'),
                                 validators=[RegexValidator('\w+(\s\w)*')])
        admin_group = forms.ModelMultipleChoiceField(Group.objects.all(), label=_('Groups allowed to upload packages'),
                                                     required=False)
        reader_group = forms.ModelMultipleChoiceField(Group.objects.all(), widget=forms.HiddenInput(),
                                                      label=_('Groups allowed to download packages'),
                                                      help_text=_('Only if downloads require authentication'), required=False)

    return RepositoryForm


CONFIRM_PHRASE = _('yes, I want to delete this element.')


def confirm_phrase(value):
    if value != CONFIRM_PHRASE:
        raise ValidationError(_('You must confirm the deletion.'))


class DeleteRepositoryForm(forms.Form):

    confirm = forms.CharField(max_length=80, label=_('Please enter “%(confirm)s”') % {'confirm': CONFIRM_PHRASE},
                              validators=[confirm_phrase])


class RepositoryUpdateForm(forms.Form):
    on_index = forms.BooleanField(label=_('Display on index for everybody?'), initial=True, required=False)
    is_private = forms.BooleanField(label=_('Must downloads be authenticated?'), initial=False, required=False, widget=forms.HiddenInput())
    states = forms.CharField(label=_('Possible states'), initial='dev qualif prod',
                             help_text=_('Please separate values by spaces'),
                             validators=[RegexValidator('\w+(\s\w)*')])
    admin_group = forms.ModelMultipleChoiceField(Group.objects.all(), label=_('Groups allowed to upload'),
                                                 required=False)
    # reader_group = forms.ModelMultipleChoiceField(Group.objects.all(), widget=forms.HiddenInput(),
    #                                               help_text=_('Only if downloads are authenticated'),
    #                                               label=_('Groups allowed to download packages'), required=False)


class SignatureForm(forms.Form):
    sha256 = forms.CharField(label=_('SHA256'), max_length=255, validators=[RegexValidator(r'\w{64}')])
    method = forms.ChoiceField(label=_('Method'), choices=ElementSignature.METHODS)
