from django import forms
from django.forms.models import modelformset_factory
from django.utils.translation import ugettext as _

from projector.models import Membership
from projector.models import Project
from projector.models import Task
from projector.models import Status
from projector.models import Component
from projector.models import Milestone

from vcs.web.simplevcs.models import Repository
from richtemplates.forms import LimitingModelForm, RestructuredTextAreaField,\
    UserByNameField

import logging

PUBLIC_RADIO_CHOICES = (
    (u'public', _("Public")),
    (u'private', _("Private"))
)

class ProjectForm(forms.ModelForm):
    name = forms.CharField(min_length=2, max_length=64, label=_('Name'))
    public = forms.ChoiceField(label=_("Visibility"),
        choices=PUBLIC_RADIO_CHOICES,
        widget=forms.RadioSelect(),
        initial=u'private',
    )

    class Meta:
        model = Project
        exclude = ('members', 'author', 'editor', 'repository')

    def clean_public(self):
        data = self.cleaned_data['public']
        # Returned data depends on PUBLIC_RADIO_CHOICES
        if data == u'public':
            return True
        elif data == u'private':
            return False
        else:
            raise forms.ValidationError(_("Choose one of the given options"))

class TaskCommentForm(forms.Form):
    comment = forms.CharField(label=_("Comment"), widget=forms.Textarea,
        required=False)

class TaskForm(LimitingModelForm):
    owner = UserByNameField(max_length=128, label=_('Owner'), required=False)
    deadline = forms.DateField(required=False, label=_("Deadline"),
        widget=forms.DateInput(attrs={'class': 'datepicker'}))

    class Meta:
        model = Task
        exclude = ['author', 'author_ip', 'project', 'editor', 'editor_ip']
        choices_limiting_fields = ['project']

    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        # Update ``status`` field while creating new task
        self.fields['status'].queryset = Status.objects.filter(
            project=self.instance.project, is_initial=True)
        self.fields['status'].empty_label=None
        self.fields['owner'].queryset = self.instance.project.members.all()

    def clean(self):
        cleaned_data = super(TaskForm, self).clean()
        if self.instance.id:
            if not Task.diff(new=self.instance):
                raise forms.ValidationError(_("No changes made"))
        return cleaned_data

    def save(self, editor, editor_ip, project=None, commit=True):
        assert project or self.instance.project,\
            "For new tasks you have to pass project object into this method."
        if project:
            self.instance.project = project
        self.instance.editor = editor
        self.instance.editor_ip = editor_ip
        if not self.instance.id:
            # For new tasks we basically treat editor as the author
            self.instance.author = editor
            self.instance.author_ip = editor_ip
        id = self.instance._calculate_id()
        logging.debug("Calculated id: %s" % id)
        return super(TaskForm, self).save(commit)

class TaskEditForm(TaskForm):
    deadline = forms.DateField(required=False, label=_("Deadline"),
        widget=forms.DateInput(attrs={'class': 'datepicker'}))
    description = RestructuredTextAreaField(max_length=3000,
        label=_('Description'))
    comment = RestructuredTextAreaField(max_length=3000,
        label=_('Comment'), widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        super(TaskEditForm, self).__init__(*args, **kwargs)
        if 'status' in self.fields:
            status_field = self['status'].field
            status_field.queryset = self.instance.status.destinations.all()

    def clean(self):
        cleaned_data = self.cleaned_data
        logging.debug("cleaned_data:\n%s" % cleaned_data)
        if not cleaned_data.get('comment'):
            cleaned_data = super(TaskEditForm, self).clean()
        return cleaned_data

class MembershipForm(LimitingModelForm):
    member = UserByNameField(max_length=128, label=_("Member"))

    class Meta:
        model = Membership
        exclude = ['project']
        choices_limiting_fields = ['project']

    def clean_member(self, commit=True):
        member = self.cleaned_data['member']
        if Membership.objects.filter(
            member = member,
            project = self.instance.project,
        ).count() > 0:
            raise forms.ValidationError(_("This user is already member of "
                "this project"))
        return member

class MilestoneForm(forms.ModelForm):
    deadline = forms.DateField(required=False, label=_("Deadline"),
        widget=forms.DateInput(attrs={'class': 'datepicker'}))


    class Meta:
        model = Milestone
        exclude = ['project', 'author']

class ComponentForm(forms.ModelForm):

    class Meta:
        model = Component
        exclude = ['project']

class StatusEditForm(forms.ModelForm):

    class Meta:
        model = Status
        exclude = ['project']

    def clean(self):
        cleaned_data = self.cleaned_data
        try:
            Status.objects.get(name__iexact=cleaned_data['name'],
                project=self.instance.project)
        except Status.DoesNotExist:
            pass
        else:
            raise forms.ValidationError(_("Status with this name already "
                "exists for this project"))
        return cleaned_data

class StatusForm(StatusEditForm):

    class Meta:
        model = Status
        exclude = ['project', 'destinations']

StatusFormSetBase = modelformset_factory(Status,
    exclude = ['description', 'project'],
    extra = 0,
)

class StatusFormSet(StatusFormSetBase):

    def add_fields(self, form, index):
        super(StatusFormSet, self).add_fields(form, index)
        qs = form['destinations'].field.queryset
        if form.instance.project:
            qs = qs.filter(project = form.instance.project)
            form['destinations'].field.queryset = qs

