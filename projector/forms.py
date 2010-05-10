from django import forms
from django.forms.models import modelformset_factory
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User, Group
from django.contrib import messages

from projector.models import Membership
from projector.models import Team
from projector.models import Project
from projector.models import Task
from projector.models import Status
from projector.models import Component
from projector.models import Milestone
from projector.utils.basic import codename_to_label

from livesettings import config_value

from richtemplates.forms import LimitingModelForm, RestructuredTextAreaField,\
    ModelByNameField
from richtemplates.widgets import RichCheckboxSelectMultiple

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
        exclude = ('members', 'author', 'editor', 'repository', 'teams')

    def clean_public(self):
        data = self.cleaned_data['public']
        # Returned data depends on PUBLIC_RADIO_CHOICES
        if data == u'public':
            return True
        elif data == u'private':
            return False
        else:
            raise forms.ValidationError(_("Choose one of the given options"))

    def clean_teams(self):
        # Not used with ``teams`` field excluded
        data = self.cleaned_data['teams']
        logging.info(data)
        teams = [Team(group=group) for group in
            data]
        return teams

    def save(self, commit=True):
        instance = super(ProjectForm, self).save(commit=False)
        if commit:
            instance.save()
            for team in self.cleaned_data.get('teams', ()):
                team.project = instance
                team.save()
        return instance

class TaskCommentForm(forms.Form):
    comment = forms.CharField(label=_("Comment"), widget=forms.Textarea,
        required=False)

class TaskForm(LimitingModelForm):
    owner = ModelByNameField(max_length=128, queryset=User.objects.all,
        attr='username', label=_('Owner'), required=False)
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
    member = ModelByNameField(max_length=128, queryset=User.objects.all,
        attr='username', label=_("Member"))

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

class ProjectMembershipPermissions(forms.Form):
    permissions = forms.MultipleChoiceField(
        choices = ((codename, codename_to_label(codename)) for codename in
            config_value('PROJECTOR', 'MEMBERSHIP_EDITABLE_PERMISSIONS')),
        label = _("Permissions"),
        widget = RichCheckboxSelectMultiple,
        required = False)

    def __init__(self, data=None, initial_permissions=[], membership=None,
            request=None):
        super(ProjectMembershipPermissions, self).__init__(data)
        self.membership = membership
        self.fields['permissions'].initial = initial_permissions
        self.request = request

    def _message(self, level, message):
        # If request was set on form, will use messages framework
        assert level in ('success', 'warning', 'info', 'error')
        if self.request:
            getattr(messages, level)(self.request, message)

    def save(self, request, commit=True):
        """
        Saves granted permissions and removes those switched off.
        """
        from projector.permissions import get_or_create_permisson
        from projector.permissions import remove_permission
        granted_codenames = self.cleaned_data['permissions']
        member_perms = self.membership.all_perms
        current_codenames = [p.codename for p in member_perms]
        # Grant permissions
        for codename in granted_codenames:
            if codename not in current_codenames:
                get_or_create_permisson(
                    codename = codename,
                    obj = self.membership.project,
                    user = self.membership.member,
                    creator = request.user,
                )
                self._message('info', _("Permission added: %s" % codename))
        # Remove permissions
        for codename in current_codenames:
            if codename not in granted_codenames:
                remove_permission(
                    codename = codename,
                    obj = self.membership.project,
                    user = self.membership.member,
                )
                self._message('error', _("Permission removed: %s" % codename))
        # if permission stays after removal - member probably got perm from
        # his/her team

    def get_codenames(self):
        """
        Returns codenames of editable permissions.
        """
        return [choice[0] for choice in self.fields['permissions'].choices]

class TeamForm(LimitingModelForm):
    group = ModelByNameField(queryset=Group.objects.all,
        max_length=64, label=_("Group"))

    class Meta:
        model = Team
        exclude = ['project']
        choices_limiting_fields = ['project']

    def clean_group(self):
        group = self.cleaned_data['group']
        if Team.objects.filter(
            group = group,
            project = self.instance.project,
        ).count() > 0:
            raise forms.ValidationError(_("This group is already a team "
                "of this project"))
        return group


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

    def clean_name(self):
        name = self.cleaned_data['name']
        if self.instance.project.component_set\
            .filter(name__iexact=name)\
            .exists():
            raise forms.ValidationError(_("Component with same name already "
                "defined for this project"))
        return name

class StatusEditForm(forms.ModelForm):

    class Meta:
        model = Status
        exclude = ['project']

    def clean_name(self):
        name = self.cleaned_data['name']
        try:
            Status.objects.get(name__iexact=name,
                project=self.instance.project)
        except Status.DoesNotExist:
            pass
        else:
            raise forms.ValidationError(_("Status with this name already "
                "exists for this project"))
        return name

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

