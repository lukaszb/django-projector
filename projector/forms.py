from django import forms
from django.forms.models import modelformset_factory
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User, Group
from django.contrib import messages

from guardian.shortcuts import assign, remove_perm, get_perms,\
    get_perms_for_model

from projector.models import Membership
from projector.models import Team
from projector.models import Project
from projector.models import Config
from projector.models import Task
from projector.models import Status
from projector.models import Component
from projector.models import Milestone
from projector.models import UserProfile
from projector.settings import get_config_value

from richtemplates.forms import LimitingModelForm, RestructuredTextAreaField,\
    ModelByNameField
from richtemplates.widgets import RichCheckboxSelectMultiple
from richtemplates.forms import RichSkinChoiceField, RichCodeStyleChoiceField

import logging

PUBLIC_RADIO_CHOICES = [
    (u'public', _("Public")),
    (u'private', _("Private"))
]

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

    def __init__(self, *args, **kwargs):
        res = super(ProjectForm, self).__init__(*args, **kwargs)
        # Update ``status`` field while creating new task
        if get_config_value('PRIVATE_ONLY'):
            self.fields['public'].choices.pop(0)
        return res

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

class ConfigForm(forms.ModelForm):
    changesets_paginate_by = forms.IntegerField(
        label=_('Changesets paginate by'), min_value=5, max_value=50)


    class Meta:
        model = Config
        exclude = ['project', 'editor']

class TaskCommentForm(forms.Form):
    comment = forms.CharField(label=_("Comment"), widget=forms.Textarea,
        required=False)

class TaskForm(LimitingModelForm):
    owner = ModelByNameField(max_length=128, queryset=User.objects.all,
        attr='username', label=_('Owner'), required=False)
    deadline = forms.DateField(required=False, label=_("Deadline"),
        widget=forms.DateInput(attrs={'class': 'datepicker'}))
    watch_changes = forms.BooleanField(False, label=_('Watch for changes'),
        initial=True)

    class Meta:
        model = Task
        exclude = ['author', 'author_ip', 'project', 'editor', 'editor_ip']
        choices_limiting_fields = ['project']

    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        if 'status' in self.fields:
            # Update ``status`` field while creating new task
            self.fields['status'].queryset = Status.objects.filter(
                project=self.instance.project, is_initial=True)
            self.fields['status'].empty_label=None
        #self.fields['owner'].queryset = self.instance.project.members.all()

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
        task = super(TaskForm, self).save(commit)
        if commit and self.cleaned_data['watch_changes']:
            task.watch(editor)
        return task

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
        if 'watch_changes' in self.fields:
            self.fields.pop('watch_changes')

    def clean(self):
        comment = self.cleaned_data.get('comment', None)
        logging.debug("Setting comment to: %s" % comment)
        self.instance.comment = comment
        return super(TaskEditForm, self).clean()

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

def get_editable_perms():
    editable_perms = get_config_value('EDITABLE_PERMISSIONS')
    perms = [(p.codename, p.name) for p in get_perms_for_model(Project)
        if p.codename in editable_perms]
    perms.sort(key=lambda pair: pair[0])
    return perms

class MembershipDeleteForm(forms.Form):
    post = forms.BooleanField(initial=True, widget=forms.HiddenInput)

class ProjectMembershipPermissionsForm(forms.Form):
    permissions = forms.MultipleChoiceField(
        choices = (), # fetch for every instance (see __init__)
        label = _("Permissions"),
        widget = RichCheckboxSelectMultiple,
        required = False)

    def __init__(self, data=None, initial_permissions=[], membership=None,
            request=None, send_messages=False):
        super(ProjectMembershipPermissionsForm, self).__init__(data)
        self.membership = membership
        self['permissions'].field.choices = get_editable_perms()
        self.fields['permissions'].initial = initial_permissions
        self.request = request
        self.send_messages = send_messages

    def _message(self, level, message):
        assert level in ('success', 'warning', 'info', 'error')
        if self.request and self.send_messages:
            getattr(messages, level)(self.request, message)

    def save(self, commit=True):
        """
        Saves granted permissions and removes those switched off.
        """
        member, project = self.membership.member, self.membership.project

        granted_perms = self.cleaned_data['permissions']
        logging.info("Granted perms: %s" % granted_perms)
        member_perms = get_perms(member, project)
        # Grant permissions
        for perm in granted_perms:
            if perm not in member_perms:
                assign(perm, member, project)
                self._message('info', _("Permission added: %s" % perm))
        # Remove permissions
        for perm in member_perms:
            if perm not in granted_perms:
                remove_perm(perm, member, project)
                # notify user if perm is still granted by member's groups
                groups_with_perm = member.groups.filter(
                    groupobjectpermission__permission__codename=perm)
                if groups_with_perm:
                    messages.warning(self.request, _("Permission %(perm)s is "
                        "still granted for %(user)s as following group(s) "
                        "has/have it: %(groups)s" % {
                            'perm': perm,
                            'user': member,
                            'groups': ', '.join(
                                (str(group) for group in groups_with_perm)
                            )
                        }))
                self._message('warning', _("Permission removed: %s" % perm))

class ProjectTeamPermissionsForm(forms.Form):
    permissions = forms.MultipleChoiceField(
        choices = get_editable_perms(),
        label = _("Permissions"),
        widget = RichCheckboxSelectMultiple,
        required = False)

    def __init__(self, data=None, initial_permissions=[], team=None,
            request=None, send_messages=False):
        super(ProjectTeamPermissionsForm, self).__init__(data)
        self.team = team
        self.fields['permissions'].initial = initial_permissions
        self.request = request
        self.send_messages = send_messages

    def _message(self, level, message):
        assert level in ('success', 'warning', 'info', 'error')
        if self.request and self.send_messages:
            getattr(messages, level)(self.request, message)

    def save(self, commit=True):
        """
        Saves granted permissions and removes those switched off.
        """
        group, project = self.team.group, self.team.project

        granted_perms = self.cleaned_data['permissions']
        team_perms = get_perms(group, project)
        # Grant permissions
        for perm in granted_perms:
            if perm not in team_perms:
                assign(perm, group, project)
                self._message('info', _("Permission added: %s" % perm))
        # Remove permissions
        for perm in team_perms:
            if perm not in granted_perms:
                remove_perm(perm, group, project)
                self._message('warning', _("Permission removed: %s" % perm))

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


class TeamDeleteForm(forms.Form):
    post = forms.BooleanField(initial=True, widget=forms.HiddenInput)

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
        if not self.instance.pk and self.instance.project.component_set\
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

class UserProfileForm(forms.ModelForm):
    skin = RichSkinChoiceField()
    code_style = RichCodeStyleChoiceField()

    class Meta:
        model = UserProfile
        exclude = ('user', 'activation_token')

