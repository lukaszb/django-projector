from django import forms
from django.forms.util import ErrorList
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

from richtemplates.forms import DynamicActionChoice
from richtemplates.forms import DynamicActionFormFactory
from richtemplates.forms import LimitingModelForm

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
    owner = UserByNameField(max_length=128, label=_('Owner'))

    class Meta:
        model = Task
        exclude = ['author', 'author_ip', 'project', 'editor', 'editor_ip',
                'status']
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
    comment = forms.CharField(max_length=3000, widget=forms.Textarea,
        required=False)

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

    class Meta:
        model = Milestone
        exclude = ['project', 'author']

