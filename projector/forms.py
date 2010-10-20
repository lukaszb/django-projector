import logging

from django import forms
from django.forms.models import modelformset_factory
from django.forms.models import BaseModelFormSet
from django.utils.translation import ugettext as _
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.contrib.formtools.wizard import FormWizard
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import redirect

from guardian.shortcuts import assign, remove_perm, get_perms,\
    get_perms_for_model

from projector.core.exceptions import ProjectorError
from projector.forks.base import BaseExternalForkForm
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
from projector.signals import setup_project
from projector.utils.basic import str2obj

from richtemplates.forms import LimitingModelForm, RestructuredTextAreaField,\
    ModelByNameField, UserByNameField
from richtemplates.widgets import RichCheckboxSelectMultiple
from richtemplates.forms import RichSkinChoiceField, RichCodeStyleChoiceField

from vcs.backends import get_supported_backends


PUBLIC_RADIO_CHOICES = [
    (u'public', _("Public")),
    (u'private', _("Private"))
]

class PerProjectUniqueNameMixin(object):
    """
    Can be used for forms with model which is related with Project and has
    ``name`` field which should be unique per project.
    """
    def clean_name(self):
        name = self.cleaned_data['name']
        if self._meta.model.objects\
            .filter(project=self.instance.project)\
            .filter(name__iexact=name)\
            .exists():
            raise forms.ValidationError(_("%(class)s with same name already "
                "defined for this project" % {
                    'class': self._meta.model.__name__}))
        return name

enabled_backends = get_config_value('ENABLED_VCS_BACKENDS')
supported_backends = get_supported_backends()
if not set(enabled_backends).issubset(set(supported_backends)):
    raise ImproperlyConfigured("VCS supports only following backends: %s"
        % ', '.join(supported_backends))

VCS_BACKENDS_CHOICES = ((key, key) for key in enabled_backends)

class ProjectBaseForm(forms.ModelForm):
    name = forms.CharField(min_length=2, max_length=64, label=_('Name'))
    public = forms.ChoiceField(label=_("Visibility"),
        choices=PUBLIC_RADIO_CHOICES,
        widget=forms.RadioSelect(),
        initial=u'private',
    )
    class Meta:
        model = Project
        exclude = ('members', 'author', 'editor', 'repository', 'teams',
            'parent', 'fork_url', 'is_active', 'category', 'state',
            'error_text')

    def __init__(self, *args, **kwargs):
        form = super(ProjectBaseForm, self).__init__(*args, **kwargs)
        # Update ``status`` field while creating new task
        if get_config_value('PRIVATE_ONLY'):
            self.fields['public'].choices = PUBLIC_RADIO_CHOICES[1:]
        return form

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

    def clean_name(self):
        name = self.cleaned_data['name']
        if name.strip().lower() in get_config_value('BANNED_PROJECT_NAMES'):
            raise forms.ValidationError(_("This name is restricted"))
        if Project.objects\
                .filter(name=name, author=self.instance.author)\
                .exclude(pk=self.instance.pk).exists():
            msg = _("You have project with same name already")
            raise forms.ValidationError(msg)
        return name


class ProjectCreateForm(ProjectBaseForm):
    vcs_alias = forms.ChoiceField(choices=VCS_BACKENDS_CHOICES,
        label=_('Version Control Backend'),
        initial=get_config_value('DEFAULT_VCS_BACKEND'))

    def save(self, commit=True):
        instance = super(ProjectCreateForm, self).save(commit=False)
        if commit:
            instance.save()
            setup_project.send(sender=Project, instance=instance,
                vcs_alias=self.cleaned_data.get('vcs_alias', None))
            for team in self.cleaned_data.get('teams', ()):
                team.project = instance
                team.save()
        return instance


class ProjectEditForm(ProjectBaseForm):
    pass


class ProjectForkForm(forms.Form):
    """
    Currently dummy form which is enough for fork page.
    """
    pass


class ConfigForm(forms.ModelForm):
    """
    ModelForm for :model:`Config`.
    """
    changesets_paginate_by = forms.IntegerField(
        label=_('Changesets paginate by'), min_value=5, max_value=50)


    class Meta:
        model = Config
        exclude = ['project', 'editor', 'from_email_address']


class TaskForm(LimitingModelForm):
    owner = ModelByNameField(max_length=128, queryset=User.objects.all,
        attr='username', label=_('Owner'), required=False)
    deadline = forms.DateField(required=False, label=_("Deadline"),
        widget=forms.DateInput(attrs={'class': 'datepicker'}))
    watch_changes = forms.BooleanField(False, label=_('Watch for changes'),
        initial=True)
    description = RestructuredTextAreaField(max_length=3000,
        label=_('Description'))

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
        if commit and self.cleaned_data.get('watch_changes', False):
            task.watch(editor)
        return task


class TaskEditForm(TaskForm):
    deadline = forms.DateField(required=False, label=_("Deadline"),
        widget=forms.DateInput(attrs={'class': 'datepicker'}))
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


class MilestoneForm(forms.ModelForm, PerProjectUniqueNameMixin):
    created_at = forms.DateField(required=False, label=_("Start date"),
        widget=forms.DateInput(attrs={'class': 'datepicker'}))
    deadline = forms.DateField(required=False, label=_("Deadline"),
        widget=forms.DateInput(attrs={'class': 'datepicker'}))

    class Meta:
        model = Milestone
        exclude = ['project', 'author']


class ComponentForm(forms.ModelForm, PerProjectUniqueNameMixin):

    class Meta:
        model = Component
        exclude = ['project']


class StatusEditForm(forms.ModelForm, PerProjectUniqueNameMixin):

    class Meta:
        model = Status
        exclude = ['project']


class StatusForm(StatusEditForm):

    class Meta:
        model = Status
        exclude = ['project', 'destinations']


class BaseStatusFormSet(BaseModelFormSet):

    def clean(self):
        """
        Checks that no two statuses have the same name.
        """
        if any(self.errors):
            # Don't bother validating the formset unless each form is valid on
            # its own
            return
        # TODO: Notify user which forms were posted with same names (use
        # form._errors['name'] = ... )
        names = []
        for form in self.forms:
            name = form.cleaned_data['name']
            if name in names:
                raise forms.ValidationError(_("Statuses in a set must have "
                    "distinct name"))
            names.append(name)

    def add_fields(self, form, index):
        super(BaseStatusFormSet, self).add_fields(form, index)
        qs = form['destinations'].field.queryset
        if form.instance.project:
            qs = qs.filter(project = form.instance.project)
            form['destinations'].field.queryset = qs

StatusFormSet = modelformset_factory(Status,
    exclude = ['description', 'project'],
    extra = 0,
    formset = BaseStatusFormSet,
)

class UserProfileForm(forms.ModelForm):
    skin = RichSkinChoiceField()
    code_style = RichCodeStyleChoiceField()

    class Meta:
        model = UserProfile
        exclude = ('user', 'activation_token', 'is_team', 'group')


class UserConvertToTeamForm(forms.Form):
    """
    Simple form which converts user into :model:`Team`.

    .. note::
       User instance has to be set within a view::

          def aview(request):
              form = UserConvertToTeamForm(request.POST or None)
              form.user = request.user
              # ...

    .. seealso:: :ref:`teamwork-membership-convert`

    """
    confirm = forms.BooleanField(label=_('confirm'))

    def _get_user(self):
        return getattr(self, '_user', None)

    def _set_user(self, user):
        self._user = user

    user = property(_get_user, _set_user)

    def clean(self):
        """
        Cleans ``confirm`` field. If checked and ``user`` attribute has been
        set, :manager:`TeamManager`'s method ``convert_from_user`` is called.
        """
        if any(self.errors):
            return
        if not self.user:
            self._errors['confirm'] = [_("No user has been set")]
            raise forms.ValidationError()
        Team.objects.convert_from_user(self.user)
        return super(UserConvertToTeamForm, self).clean()

map = get_config_value('FORK_EXTERNAL_MAP')
fork_map = dict((key, str2obj(val)) for key, val in map.items())
choices = tuple((key, key) for key in fork_map)


class ExternalForkSourcesForm(forms.Form):
    source = forms.ChoiceField(choices=choices)


class ExternalForkWizard(FormWizard):
    """
    Form wizard which processes each step of external forking.

    .. seealso:: :ref:`projects-forking-external`

    """

    def done(self, request, form_list):
        form = form_list[1]
        form.request = request
        try:
            fork = form.fork()
        except ProjectorError, err:
            msg = _("Error occured while trying to fork %s" % form.get_url())
            messages.error(request, msg)
            logging.error(str(err))
            return redirect('projector_dashboard')
        else:
            return redirect(fork.get_absolute_url())

    def process_step(self, request, form, step):
        form.is_valid()
        if step == 0:
            source = form.cleaned_data['source']
            self.form_list[1] = fork_map[source]
            # TODO: Setting request here is kind of *magic*
            self.form_list[1].request = request
        elif step == 1:
            if not isinstance(form, BaseExternalForkForm):
                raise ProjectorError(
                        "Final fork wizard form must be subclass of "
                        "projector.forks.base.BaseForkForm class")
        return super(ExternalForkWizard, self).process_step(request, form, step)

    def get_template(self, step):
        return 'projector/accounts/dashboard-external-fork.html'


class DashboardAddMemberForm(forms.Form):
    """
    Form providing ability to add user to the group. It is useful for users
    converted into :model:`Team` to add new members.
    """
    user = UserByNameField()

    def __init__(self, group, *args, **kwargs):
        self.group = group
        super(DashboardAddMemberForm, self).__init__(*args, **kwargs)

    def clean_user(self):
        """
        Raises ``ValidationError`` if user is already member of given group or
        user does not exist.
        """
        user = self.cleaned_data['user']
        if user:
            try:
                user.groups.get(name=self.group.name)
            except Group.DoesNotExist:
                pass
            else:
                raise forms.ValidationError(_("User %(user)s is already a "
                    "member of %(group)s" %
                    {'user': user, 'group': self.group}))
        return user

    def save(self, commit=True):
        """
        Adds chosen user to the group.
        """
        user = self.cleaned_data['user']
        if commit:
            user.groups.add(self.group)
        return user

