from django import forms
from django.forms.util import ErrorList
from django.forms.models import modelformset_factory
from django.contrib.admin import widgets
from django.contrib.auth.models import User
from django.contrib.formtools.wizard import FormWizard
from django.shortcuts import render_to_response
from django.utils.translation import ugettext as _

from projector.models import Membership
from projector.models import Project
from projector.models import ProjectCategory
from projector.models import Task
from projector.models import Status
from projector.models import Milestone
from projector.settings import BANNED_PROJECT_NAMES

from richtemplates.forms import LimitingModelForm, RestructuredTextAreaField

import logging

# Custom fields

class UserByNameField(forms.CharField):
    """
    Allows to choose user by simple typing his or her
    name instead of picking up from <select> tag.
    """
    def clean(self, value):
        """
        Returns user for whom task is beign assigned.
        """
        # Firstly, we have to clean as normal CharField
        value = super(UserByNameField, self).clean(value)
        # Now do the magic
        username = value.strip()
        if username == '':
            return None
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError("No user found!")
        logging.debug("Returns UserByNameField: %s" % user)
        return user

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
        exclude = ('members', 'author', 'editor', 'repository_url')

    def clean_public(self):
        data = self.cleaned_data['public']
        # Returned data depends on PUBLIC_RADIO_CHOICES
        if data == u'public':
            return True
        elif data == u'private':
            return False
        else:
            raise forms.ValidationError(_("Choose one of the given options"))

    def clean_name(self):
        name = self.cleaned_data['name']
        if name in BANNED_PROJECT_NAMES:
            raise forms.ValidationError(_("Cannot use this name"))
        return name

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
    extra = 0,
    fields = ['name', 'order', 'destinations'])

class StatusFormSet(StatusFormSetBase):

    def add_fields(self, form, index):
        super(StatusFormSet, self).add_fields(form, index)
        qs = form['destinations'].field.queryset
        if form.instance.project:
            qs = qs.filter(project = form.instance.project)
            form['destinations'].field.queryset = qs

class TaskActionFormError(Exception):
    pass

def TaskActionForm(data=None, instance=None):
    if instance is None:
        raise TaskActionFormError("instance parameter is required")

    fields = {
        'leave_status': forms.CharField(label=_("Leave status as %s"
            % instance.status), widget=forms.HiddenInput),
        'set_status': forms.ModelChoiceField(label=_("Set status to"),
            empty_label=None,
            queryset=instance.status.destinations.all())
    }
    # Removes requirements from all fields
    for field_name, field in fields.items():
        field.required = False
        fields[field_name] = field

    action_fields = ['leave_status', 'set_status']
    action_group = 'action_type' #

    if not set(action_fields).issubset(set(fields.keys())):
        raise TaskActionFormError("Action fields have to be subset of "
            "base fields")

    action_type = forms.TypedChoiceField(
        choices=[(i, field.label) for i, field in enumerate(fields.values())],
        initial=1, # Hard coded :/
        widget=forms.RadioSelect,
        coerce=int
    )

    def clean(self):
        cleaned_data = self.cleaned_data
        chosen_action = cleaned_data.get(action_group)
        if chosen_action in [None, u'']:
            raise forms.ValidationError(_("Choose action"))
        return cleaned_data



    def save(self, editor, editor_ip, commit=True):
        if self.is_valid():
            self.instance.editor = editor
            self.instance.editor_ip = editor_ip
            #self.instance.status = self.cleaned_data['status']
            if commit:
                self.instance.save()
                return self.instance

    FormClass = type("TaskActionForm", (forms.BaseForm, ),
        {
            'base_fields': {action_group: action_type},
            'clean': clean,
            'save': save,
        }
        )
    form = FormClass(data)
    form.instance = instance

    return form



