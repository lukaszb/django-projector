import os
import sys
import string
import logging
import datetime
import traceback

from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import User, Group, AnonymousUser, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError, PermissionDenied,\
    ImproperlyConfigured
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from django.db.models.query import QuerySet
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _
from django.utils.timesince import timesince

from guardian.shortcuts import assign, get_perms, get_perms_for_model

from autoslug import AutoSlugField

from projector import settings as projector_settings
from projector.core.exceptions import ProjectorError
from projector.core.exceptions import ConfigAlreadyExist
from projector.core.exceptions import ForkError
from projector.managers import ProjectManager
from projector.managers import TaskManager
from projector.managers import TeamManager
from projector.managers import WatchedItemManager
from projector.settings import get_config_value
from projector.signals import post_fork
from projector.utils import abspath, str2obj, using_projector_profile
from projector.utils.lazy import LazyProperty
from projector.utils.helpers import Choices

from vcs.backends import get_supported_backends
from vcs.exceptions import VCSError
from vcs.web.simplevcs.models import Repository

from richtemplates.models import UserProfile as RichUserProfile

from treebeard.al_tree import AL_Node


PROJECT_VCS_ALIAS_FIELD = '_vcs_alias'
PROJECT_WORKFLOW_FIELD = '_workflow_obj'

class WatchedItem(models.Model):
    """
    Projects, Tasks and other items watched by the User.
    """
    user = models.ForeignKey(User)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    objects = WatchedItemManager()

    class Meta:
        unique_together = ('user', 'content_type', 'object_id')

    def __unicode__(self):
        return u'%s watched by %s' % (self.content_object, self.user)

class Watchable(object):
    def watch(self, user):
        item, created = WatchedItem.objects.get_or_create(
            user = user,
            content_type = ContentType.objects.get_for_model(self),
            object_id = self.pk,
        )
        return item, created

    def unwatch(self, user):
        WatchedItem.objects.filter(
            user = user,
            content_type = ContentType.objects.get_for_model(self),
            object_id = self.pk,
        ).delete()

    def is_watched(self, user):
        if isinstance(user, AnonymousUser):
            return False
        try:
            WatchedItem.objects.get(
                user = user,
                content_type = ContentType.objects.get_for_model(self),
                object_id = self.pk)
            return True
        except WatchedItem.DoesNotExist:
            return False

    def get_watchers(self):
        users = User.objects.filter(
            watcheditem__content_type = ContentType.objects.get_for_model(self),
            watcheditem__object_id = self.pk,
        )
        return users

class DictModel(models.Model):
    name = models.CharField(_('name'), max_length=32)
    description = models.TextField(_('description'), null=True, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True
        ordering = ('id',)

class OrderedDictModel(DictModel):
    """
    DictModel with order column and default ordering.
    """
    order = models.IntegerField(_('order'))

    class Meta:
        abstract = True
        ordering = ['order', 'name']

class ProjectCategory(models.Model):
    name = models.CharField(_('name'), max_length=64, unique=True)
    slug = models.SlugField(unique=True, editable=False, max_length=64)
    public = models.BooleanField(_('public'), default=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('project')
        verbose_name_plural = _('project categories')

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.slug = slugify(self.name)
        super(ProjectCategory, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return ('projector_project_category_detail', (), {
            'username': self.project.author.username,
            'project_category_slug' : self.slug,
        })

def validate_project_name(name):
    """
    Checks if this project name may be used.
    """
    if name.strip().lower() in projector_settings.BANNED_PROJECT_NAMES:
        raise ValidationError(_("This name is restricted"))


class State(Choices):
    """
    Represents state of the project.
    """
    ERROR = -1
    PENDING = 0
    CREATED = 10
    MEMBERSHIPS_CREATED = 20
    AUTHOR_PERMISSIONS_CREATED = 30
    WORKFLOW_CREATED = 40
    CONFIG_CREATED = 50
    REPOSITORY_CREATED = 60
    READY = 100


class Project(AL_Node, Watchable):
    """
    Most important model within whole application. It provides connection with
    all other models.
    """

    name = models.CharField(_('name'), max_length=64,
        validators=[validate_project_name])
    slug = AutoSlugField(max_length=128, populate_from='name',
        unique_with='author', validators=[validate_project_name])
    category = models.ForeignKey(ProjectCategory, verbose_name=_('category'),
        null=True, blank=True)
    description = models.TextField(_('description'), null=True, blank=True)
    home_page_url = models.URLField(_("home page url "), null=True, blank=True,
        verify_exists=False)
    is_active = models.BooleanField(_('is active'), default=True)
    public = models.BooleanField(_('public'), default=True)
    members = models.ManyToManyField(User, verbose_name=_('members'),
        through="Membership")
    teams = models.ManyToManyField(Group, verbose_name=_('teams'),
        through="Team", null=True, blank=True)
    author = models.ForeignKey(User, name=_('author'),
        related_name='created_projects')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(_('modified at'), auto_now=True)
    outdated = models.BooleanField(_('outdated'), default=False)
    repository = models.ForeignKey(Repository, null=True, blank=True,
        verbose_name=_("repository"), default=None)
    state = models.IntegerField(_('state'), choices=State.as_choices(),
        default=0)
    error_text = models.CharField(_('error text'), max_length=256, null=True,
        blank=True)

    parent = models.ForeignKey('self', related_name='children_set',
       null=True, blank=True, db_index=True)
    fork_url = models.URLField(verify_exists=False, null=True, blank=True)

    node_order_by = ['author', 'name']

    objects = ProjectManager()

    class Meta:
        verbose_name = _('project')
        verbose_name_plural = _('projects')
        ordering = ['name']
        get_latest_by = 'created_at'
        unique_together = ['author', 'name']
        permissions = (
            ('view_project', 'Can view project'),
            ('admin_project', 'Can administer project'),
            ('can_read_repository', 'Can read repository'),
            ('can_write_to_repository', 'Can write to repository'),
            ('can_change_description', 'Can change description'),
            ('can_change_category', 'Can change category'),
            ('can_add_task', 'Can add task'),
            ('can_change_task', 'Can change task'),
            ('can_delete_task', 'Can delete task'),
            ('can_view_tasks', 'Can view tasks'),
            ('can_add_member', 'Can add member'),
            ('can_change_member', 'Can change member'),
            ('can_delete_member', 'Can delete member'),
            ('can_add_team', 'Can add team'),
            ('can_change_team', 'Can change team'),
            ('can_delete_team', 'Can delete team'),
        )

    def __unicode__(self):
        return self.name

    def is_public(self):
        return self.public

    def is_private(self):
        return not self.public

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        self.full_clean()
        project = super(Project, self).save(*args, **kwargs)
        # Add necessary permissions for author - we need to do this
        # *NOT* asynchronousely as instant redirect after project creation
        # may cause it's author not to be able to see project page
        return project

    @models.permalink
    def get_absolute_url(self):
        return ('projector_project_detail', (), {
            'username': self.author.username,
            'project_slug' : self.slug,
        })

    @models.permalink
    def get_edit_url(self):
        return ('projector_project_edit', (), {
            'username': self.author.username,
            'project_slug' : self.slug,
        })

    @models.permalink
    def get_state_url(self):
        return ('projector_project_state', (), {
            'username': self.author.username,
            'project_slug': self.slug,
        })

    @models.permalink
    def get_fork_url(self):
        return ('projector_project_fork', (), {
            'username': self.author.username,
            'project_slug' : self.slug,
        })

    @models.permalink
    def get_members_url(self):
        return ('projector_project_member', (), {
            'username': self.author.username,
            'project_slug' : self.slug,
        })

    @models.permalink
    def get_members_add_url(self):
        return ('projector_project_member_add', (), {
            'username': self.author.username,
            'project_slug' : self.slug,
        })

    @models.permalink
    def get_members_edit_url(self, username):
        return ('projector_project_member_edit', (), {
            'username': self.author.username,
            'project_slug': self.slug,
            'member_username': username,
        })

    @models.permalink
    def get_members_delete_url(self, username):
        return ('projector_project_member_delete', (), {
            'username': self.author.username,
            'project_slug': self.slug,
            'member_username': username,
        })

    @models.permalink
    def get_teams_url(self):
        return ('projector_project_teams', (), {
            'username': self.author.username,
            'project_slug': self.slug,
        })

    @models.permalink
    def get_teams_add_url(self):
        return ('projector_project_teams_add', (), {
            'username': self.author.username,
            'project_slug': self.slug,
        })

    @models.permalink
    def get_teams_edit_url(self, name):
        return ('projector_project_teams_edit', (), {
            'username': self.author.username,
            'project_slug': self.slug,
            'name': name,
        })

    @models.permalink
    def get_create_task_url(self):
        return ('projector_task_create', (), {
            'username': self.author.username,
            'project_slug': self.slug,
        })

    @models.permalink
    def get_task_list_url(self):
        return ('projector_task_list', (), {
            'username': self.author.username,
            'project_slug': self.slug,
        })

    @models.permalink
    def get_milestones_url(self):
        return ('projector_project_milestones', (), {
            'username': self.author.username,
            'project_slug': self.slug,
        })

    @models.permalink
    def get_milestone_gantt_url(self):
        return ('projector_project_milestones_gantt', (), {
            'username': self.author.username,
            'project_slug': self.slug,
        })

    @models.permalink
    def get_milestone_add_url(self):
        return ('projector_project_milestone_add', (), {
            'username': self.author.username,
            'project_slug': self.slug,
        })

    @models.permalink
    def get_components_url(self):
        return ('projector_project_components', (), {
            'username': self.author.username,
            'project_slug': self.slug,
        })

    @models.permalink
    def get_component_add_url(self):
        return ('projector_project_component_add', (), {
            'username': self.author.username,
            'project_slug': self.slug,
        })

    @models.permalink
    def get_workflow_url(self):
        return ('projector_project_workflow_detail', (), {
            'username': self.author.username,
            'project_slug': self.slug,
        })

    @models.permalink
    def get_workflow_edit_url(self):
        return ('projector_project_workflow_edit', (), {
            'username': self.author.username,
            'project_slug': self.slug,
        })

    @models.permalink
    def get_workflow_add_status_url(self):
        return ('projector_project_workflow_add_status', (), {
            'username': self.author.username,
            'project_slug': self.slug,
        })

    @models.permalink
    def get_browse_repo_url(self):
        return ('projector_project_sources', (), {
            'username': self.author.username,
            'project_slug': self.slug,
        })

    @models.permalink
    def get_changesets_url(self):
        return ('projector_project_changesets', (), {
            'username': self.author.username,
            'project_slug': self.slug,
        })

    def get_clone_url(self):
        if self.repository is None:
            return None
        if self.repository.alias == 'hg':
            return self.get_absolute_url()
        elif self.repository.alias == 'git':
            return reverse('projector-project-git', kwargs={
                'username': self.author.username,
                'project_slug': self.slug,
            }).rstrip('/')
        return None

    def get_repo_url(self):
        """
        Returns full url of the project (with domain based on
        django sites framework).
        """
        current_site = Site.objects.get_current()
        # FIXME: What should we do with hardcoded schemas?
        if settings.DEBUG:
            prefix = 'http://'
        else:
            prefix = 'https://'

        suffix = self.get_clone_url() or self.get_absolute_url()
        return ''.join((prefix, current_site.domain, suffix))

    def get_clone_cmd(self):
        """
        Returns client command to run in order to clone this repository.
        """
        url = self.get_repo_url()
        if self.repository.alias == 'hg':
            return 'hg clone %s' % url
        elif self.repository.alias == 'git':
            return 'git clone %s' % url.rstrip('/')
        return None

    def is_pending(self):
        return self.state != State.ERROR and self.state < State.READY

    def get_task(self, id):
        queryset = Task.objects.filter(project=self)
        if not queryset:
            # queryset at this point may be evaluated to empty list
            raise Task.DoesNotExist
        return queryset.get(id=id)

    def get_tasks(self):
        return self.task_set\
            .select_related('status', 'milestone', 'owner',
                    'priority', 'component')

    def get_open_tasks(self):
        return self.get_tasks().filter(status__is_resolved=False)

    def get_closed_tasks(self):
        return self.get_tasks().filter(status__is_resolved=True)

    def _get_homedir(self):
        """
        Returns directory containing all files related to this project. If
        repository is already set at this project, it's parent directory would
        be returned. Otherwise path is computed.

        This is semi *private* method as we cannot allow this to be called at
        templates (methods starting with underscore cannot be called within
        django templates).
        """
        if self.repository:
            return abspath(self.repository.path, '..')
        try:
            getter_path = get_config_value('PROJECTS_HOMEDIR_GETTER')
            getter = str2obj(getter_path)
        except ImportError, err:
            raise ImproperlyConfigured("PROJECTOR_PROJECTS_HOMEDIR_GETTER "
            "does not point to proper function. Error was: %s" % err)
        relative_path = getter(self)
        homedir = abspath(projector_settings.PROJECTS_ROOT_DIR, relative_path)
        if not homedir.endswith(os.path.sep):
            homedir += os.path.sep
        if os.path.exists(projector_settings.PROJECTS_ROOT_DIR) and \
            not os.path.exists(homedir):
            os.mkdir(homedir)
            logging.debug("Project '%s': Created homedir at %s"
                % (self, homedir))
        return homedir

    def _get_repo_path(self, vcs_alias=None):
        """
        Returns path to this project's repository. If repository is already set
        it's path is returned. Otherwise it is a join of *homedir* and vcs alias
        (which may be given as a parameter).
        """
        if self.repository:
            return self.repository.path
        if vcs_alias is not None:
            self.set_vcs_alias(vcs_alias)
        alias = self.get_vcs_alias()
        repo_path = abspath(self._get_homedir(), alias)
        return repo_path

    def add_timeline_entry(self, action, author):
        """
        Initially wanted to implement as models.signal handler -
        as used in django-issues. Ended up with simple wrapper
        for expending project's timeline.
        Some more logic may be added over time.
        """
        timeline_entry_info = {
            'project' : self,
            'action' : action,
            'user' : author,
        }
        obj = TimelineEntry.objects.create(**timeline_entry_info)
        logging.info("Craeted timeline entry: %s" % obj)

    def set_author_permissions(self):
        """
        Creates all permissions for project's author.

        If successful, project should change it's state to
        ``State.AUTHOR_PERMISSIONS_CREATED``. Note, that this method doesn't
        make any database related queries - state should be flushed manually.
        """
        perms = set([p.codename for p in get_perms_for_model(Project)
            if p.codename != 'add_project'])
        author_perms = set(get_perms(self.author, self))
        for perm in (perms - author_perms):
            assign(perm, self.author, self)

        # If author is Team we need to add perms to that Team too
        if self.author.get_profile().is_team:
            group = self.author.get_profile().group
            team_perms = set(get_perms(group, self))
            for perm in (perms - team_perms):
                assign(perm, self.author.get_profile().group, self)
        self.state = State.AUTHOR_PERMISSIONS_CREATED

    def set_memberships(self):
        """
        Creates :model:`Membership` for this project and it's author. If author
        is a team, we need to create :model:`Team` object too.

        If successful, project should change it's state to
        ``State.MEMBERSHIPS_CREATED``. Note, that this method doesn't make any
        database related queries - state should be flushed manually.
        """
        Membership.objects.create(project=self, member=self.author)
        if self.author.is_superuser:
            # we don't need to add permissions for superuser
            # as superusers has always all permissions
            return
        # If author is a team, we need to create :model:`Team` instance for
        # his/her group
        profile = self.author.get_profile()
        if profile.is_team:
            Team.objects.create(project=self, group=profile.group)
        logging.debug("Memberships created for project %s" % self)

    def set_workflow(self, workflow):
        setattr(self, PROJECT_WORKFLOW_FIELD, workflow)

    def get_workflow(self):
        workflow = getattr(self, PROJECT_WORKFLOW_FIELD, None)
        if workflow is None:
            workflow = str2obj(get_config_value('DEFAULT_PROJECT_WORKFLOW'))
        return workflow

    def create_workflow(self, workflow=None):
        """
        Creates default workflow for the project. We need to create objects
        required to work on issues (components, types, statuses with their
        transitions if custom workflow is used).

        Workflow is retrieved using ``get_workflow`` method on the instance but
        may be overridden by passing parameter directly.

        If successful, project should change it's state to
        ``State.WORKFLOW_CREATED``. Note, that this method doesn't make any
        database related queries - state should be flushed manually.

        :param workflow: python object defining tuples of dicts with
          information on project *metadata*; may be a string pointing to the
          object; if parameter is None, value would be retrieved using
          ``get_workflow`` instance's method
        """

        if workflow is None:
            workflow = self.get_workflow()

        for component_info in workflow.components:
            component, created = Component.objects\
                .get_or_create(project = self, **component_info)
            if created:
                logging.debug("For project '%s' new component '%s' was craeted"
                    % (component.project, component))
        for task_type_info in workflow.task_types:
            task, created = TaskType.objects\
                .get_or_create(project = self, **task_type_info)
            if created:
                logging.debug("For project '%s' new task type '%s' was craeted"
                    % (task.project, task))
        for priority_info in workflow.priorities:
            priority, created = Priority.objects\
                .get_or_create(project = self, **priority_info)
            if created:
                logging.debug("For project '%s' new priority '%s' was created."
                    % (priority.project, priority))

        for status_info in workflow.statuses:
            status, created = Status.objects\
                .get_or_create(project = self, **status_info)
            if created:
                logging.debug("For project '%s' new status '%s' was created."
                    % (status.project, status))
        # Create necessary transitions
        logging.debug("Creating transitions")
        self.create_all_transitions()

        self.state = State.WORKFLOW_CREATED

    def create_all_transitions(self):
        """
        Creates ``Transition`` objects linking all projects' statuses with
        each other providing default task *workflow* schema.
        """
        statuses = self.status_set.all()
        for status in statuses:
            for new_status in statuses:
                transition, created = Transition.objects\
                    .get_or_create(source=status, destination=new_status)
                if created:
                    logging.debug("Project '%s': created %s"
                        % (self, transition))

    def get_transitions(self):
        """
        Returns queryset of ``Transition`` objects related with this project.
        """
        transitions = Transition.objects\
            .filter(source__in=self.status_set.all())
        return transitions

    def set_vcs_alias(self, vcs_alias):
        """
        Prepares this project for repository creation process. Note that
        :error:`ProjectorError` is raised if repository for this instance has
        been already created. Same exception is raised if ``vcs`` does not support
        backend for the given alias.

        :param vcs_alias: alias for ``vcs`` backend
        """
        supported_backends = get_supported_backends()
        if vcs_alias not in supported_backends:
            raise ProjectorError("Unsupported backend %s. Supported backends "
            "have following aliases: %s" % (vcs_alias,
            ', '.join(supported_backends)))
        if self.repository is not None:
            raise ProjectorError("Cannot prepare project for repository "
            "creation if it is already set")
        setattr(self, PROJECT_VCS_ALIAS_FIELD, vcs_alias)

    def get_vcs_alias(self):
        """
        Returns vcs_alias which should be already configured for this project.
        Defaulting to :setting:`PROJECTOR_DEFAULT_VCS_BACKEND`.
        """
        if self.repository is not None:
            return self.repository.alias
        default = get_config_value('DEFAULT_VCS_BACKEND')
        vcs_alias = getattr(self, PROJECT_VCS_ALIAS_FIELD, default)
        return vcs_alias

    def create_repository(self, vcs_alias=None):
        """
        Creates repository for this project.

        ``vcs_alias`` is retrieved using ``get_vcs_alias`` method but may be
        overridden by passing parameter directly.

        If successful, project should change it's state to
        ``State.REPOSITORY_CREATED``. Note, that this method doesn't make any
        database related queries - state should be flushed manually.

        :param vcs_alias: alias for ``vcs`` backend, if None given this value
          is retrieved using ``get_vcs_alias`` instance's method

        :raise ImproperlyConfigured: if given ``vcs_alias`` is not one of
          enabled backends

        :raise ProjectorError: if repository is already created, or given
          ``vcs_alias`` is not one of vcs supported backends
        """
        if not get_config_value('CREATE_REPOSITORIES'):
            raise ProjectorError("Cannot create repository if "
            "PROJECTOR_CREATE_REPOSITORIES is not set to True")

        if self.repository is not None:
            raise ProjectorError("Cannot create repository if project has one "
            "already")

        if vcs_alias is None:
            vcs_alias = self.get_vcs_alias()

        supported_backends = get_supported_backends()
        if vcs_alias not in supported_backends:
            raise ProjectorError("Unsupported backend %s. Supported backends "
            "have following aliases: %s" % (vcs_alias,
            ', '.join(supported_backends)))

        enabled_backends = get_config_value('ENABLED_VCS_BACKENDS')
        if vcs_alias not in enabled_backends:
            raise ImproperlyConfigured("Cannot use VCS backend not specified at"
            "PROJECTOR_ENABLED_VCS_BACKENDS. Tried %s and available backends "
            "are: %s" % (vcs_alias, ', '.join(enabled_backends)))

        # Repository creation process
        try:
            clone_url = None
            if self.parent:
                # Attempt to fork internally
                clone_url = self.parent._get_repo_path()
            elif self.fork_url:
                # Attempt to fork from external location
                clone_url = self.fork_url
            repository = Repository.objects.create(
                path=self._get_repo_path(vcs_alias),
                alias=vcs_alias, clone_url=clone_url)
            # Update is much faster than save
            self.repository = repository
            Project.objects.filter(pk=self.pk).update(repository=repository)
            return repository
        except VCSError, err:
            traceback_msg = '\n'.join(traceback.format_exception(*
                (sys.exc_info())))
            msg = "Couldn't create repository"
            org_msg = msg + ". Original error was: %s" % err
            org_msg = '\n\n'.join((msg, traceback_msg))
            logging.error(org_msg)
            if settings.DEBUG:
                # Show original error only in debug mode
                raise ProjectorError(org_msg)
            else:
                raise ProjectorError(msg)
        else:
            logging.debug("%s created for project %s" % (repository, self))
            self.state = State.REPOSITORY_CREATED

    def create_config(self):
        """
        Creates default configuration for given project.

        If successful, project should change it's state to
        ``State.CONFIG_CREATED``. Note, that this method doesn't make any
        database related queries - state should be flushed manually.
        """
        if self.config_set.count() > 0:
            raise ConfigAlreadyExist("Project %s with id %d has already "
                "related configuration" % (self, self.id))
        config = Config.objects.create(
            project = self,
            editor = self.author,
        )
        logging.debug("Project '%s': created config %s" % (self, config))
        self.state = State.CONFIG_CREATED
        return config

    def get_config(self):
        """
        Returns Config for this project.
        """
        return Config.objects.get(project=self)
    config = property(get_config)

    def setup(self, vcs_alias=None, workflow=None):
        """
        Should be called **AFTER** instance is saved into database as all
        methods here creates necessary models for the project and in order
        to create relations it is needed that instance is persisted first.
        """
        # Prepare if parametrs are given. Otherwise assume that preparation
        # methods have been called already
        if vcs_alias:
            self.set_vcs_alias(vcs_alias)
        if workflow:
            self.set_workflow(workflow)

        # Fire up methods
        self.set_memberships()
        self.set_author_permissions()
        self.create_workflow()
        self.create_config()

        if get_config_value('CREATE_REPOSITORIES'):
            self.create_repository(vcs_alias)

    def get_watchers(self):
        watchers = super(Project, self).get_watchers()
        watchers = watchers.filter(models.Q(
            membership__project=self) |
            models.Q(groups__team__project=self))
        return watchers

    def fork(self, user, force_private=False):
        """
        Creates fork from internal context. As we use django-treebeard,
        we need to use it's api to create a child.

        :param user: new author for forked project
        :param force_private: if set to True, project would be created
          as private

        :returns: :py:class:`projector.models.Project`

        :raise ``django.core.exceptions.PermissionDenied``: when
          user is anonymous, not active or cannot access this project
        :raise ``projector.core.exceptions.ForkError``: when
          user has already forked this project
        """
        if user.is_anonymous() or not user.is_active:
            raise PermissionDenied("Fork is allowed for active users only")
        if not self in Project.objects.for_user(user):
            raise PermissionDenied("User is not allowed to fork this project")
        if user == self.author:
            raise ForkError("Author cannot fork own project")
        user_fork = self.get_fork_for_user(user)
        if user_fork:
            raise ForkError("User already forked this project")

        if force_private:
            is_public = False
        else:
            is_public = self.public

        project_info = {
            'name': self.name,
            'author': user,
            'public': is_public,
            'fork_url': self.get_repo_url(),
        }
        forked = self.add_child(**project_info)
        post_fork.send(sender=self, fork=forked)
        return forked

    def get_fork_for_user(self, user):
        """
        Returns fork of this project's root for the given user. If user haven't
        forked project from this instance's tree, ``None`` is returned.
        """
        for fork in self.get_all_forks():
            if fork.author_id == user.id:
                return fork
        return None

    def get_all_forks(self):
        """
        Returns all forks for this project, starting from root. Returned object
        is a list (not ``Queryset``) and contains this instance.
        """
        root = self.get_root()
        forks = Project.get_tree(parent=root)
        return forks

    def is_fork(self):
        """
        Returns ``True`` if this instance is a fork (has parent), ``False``
        otherwise.
        """
        return self.parent is not None or self.fork_url

    def get_actions(self):
        """
        Returns activity stream for this projcet.
        """
        #return Project.objects.get_actions(self)
        return self.actions.all()

    def create_action(self, verb, **kwargs):
        return Action.objects.create(project=self, verb=verb, **kwargs)


class ActionManager(models.Manager):
    def create(self, **kwargs):
        action_object = kwargs.pop('action_object', None)
        if action_object is not None:
            kwargs['action_object_content_type'] = \
                ContentType.objects.get_for_model(action_object)
            kwargs['action_object_pk'] = action_object.pk
        return super(ActionManager, self).create(**kwargs)


class Action(models.Model):
    project = models.ForeignKey(Project, verbose_name=_('Project'),
        related_name='actions')
    author = models.ForeignKey(User, null=True, blank=True,
        verbose_name=_('User'))
    verb = models.CharField(_('verb'), max_length=128)
    description = models.TextField(_('description'), null=True, blank=True)
    created_at = models.DateTimeField(_('created at'),
        default=datetime.datetime.now)
    is_public = models.BooleanField(_('is public'), default=True)

    # Optional related object
    action_object_pk = models.CharField(max_length=255, null=True, blank=True)
    action_object_content_type = models.ForeignKey(ContentType, null=True,
        blank=True, verbose_name=_('content type'))
    action_object = generic.GenericForeignKey('action_object_content_type',
        'action_object_pk')

    objects = ActionManager()

    class Meta:
        verbose_name = _('action')
        verbose_name_plural = _('actions')
        ordering = ['-created_at']
        get_latest_by = 'created_at'

    def __unicode__(self):
        if self.action_object:
            return u'%s %s %s %s ago' % (self.author, self.verb,
                self.action_object, self.timesince())
        return u'%s %s %s %s ago' % (self.author, self.verb, self.project,
            self.timesince())

    def timesince(self, now=None):
        return timesince(self.created_at, now)


class Config(models.Model):
    """
    This model stores configuration on "per project" basis.
    """
    project = models.ForeignKey(Project, unique=True, verbose_name=_('Project'))
    edited_at = models.DateTimeField(auto_now=True, verbose_name=('Edited at'))
    editor = models.ForeignKey(User)
    basic_realm = models.CharField(max_length=64, default='Basic Auth Realm',
        verbose_name = _('Basic realm'))
    always_mail_members = models.BooleanField(default = False,
        verbose_name = _('Always send mail to members'))
    changesets_paginate_by = models.PositiveIntegerField(
        verbose_name = _('Changesets paginate by'), default = 10)
    from_email_address = models.EmailField(max_length = 64,
        default = get_config_value('FROM_EMAIL_ADDRESS'),
        verbose_name = _('Email sender address'))
    #Should be scaped with from django.utils.html.escape
    task_email_summary_format = models.CharField(max_length = 128,
        default = get_config_value('TASK_EMAIL_SUBJECT_SUMMARY_FORMAT'),
        verbose_name = ('Task email summary format'),
        help_text = _(
            'You may use following placeholders: $project $summary $id'))
    milestone_deadline_delta = models.PositiveIntegerField(
        default = get_config_value('MILESTONE_DEADLINE_DELTA'),
        verbose_name = _('Milestone deadline delta'),
        help_text = _(
            u'Every milestone has its deadline and this number specifies '
            u'how many days would be given by default. It may be set to '
            u'any date during milestone creation process though.',
        ))

    def __unicode__(self):
        return u'<Config for %s>' % self.project


class Component(models.Model):
    project = models.ForeignKey(Project)
    name = models.CharField(max_length=64)
    slug = AutoSlugField(max_length=64, populate_from='name',
        always_update=True, unique_with='project')
    description = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = _('component')
        verbose_name_plural = _('components')
        ordering = ('name',)
        unique_together = ('project', 'name')

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('projector_project_component_detail', (), {
            'username': self.project.author.username,
            'project_slug': self.project.slug,
            'component_slug': self.slug,
        })

    @models.permalink
    def get_edit_url(self):
        return ('projector_project_component_edit', (), {
            'username': self.project.author.username,
            'project_slug': self.project.slug,
            'component_slug': self.slug,
        })

class Membership(models.Model):
    member = models.ForeignKey(User, verbose_name=_('member'))
    project = models.ForeignKey(Project, verbose_name=_('project'))
    joined_at = models.DateTimeField(_('joined at'), auto_now_add=True)

    def __unicode__(self):
        return u"%s@%s" % (self.member, self.project)

    class Meta:
        unique_together = ('project', 'member')

    @models.permalink
    def get_absolute_url(self):
        return ('projector_project_member_edit', (), {
            'username': self.project.author.username,
            'project_slug': self.project.slug,
            'member_username': self.member.username,
        })

    @models.permalink
    def get_delete_url(self):
        return ('projector_project_member_delete', (), {
            'username': self.project.author.username,
            'project_slug': self.project.slug,
            'member_username': self.member.username,
        })

    @LazyProperty
    def perms(self):
        """
        Returns Permission objects for member, not his/her groups.
        """
        return get_perms(self.member, self.project)

    @LazyProperty
    def all_perms(self):
        """
        Returns all Permission objects for member's and
        his/he groups (to fetch user specific permissions only, use ``perms``
        instead).
        """
        perms = Permission.objects.filter(
            models.Q(group__in = self.member.groups.all()) |
            models.Q(user=self.member)
        ).filter(
            approved = True,
            content_type = ContentType.objects.get_for_model(Project),
            object_id = self.project_id,
        )
        return perms

    @LazyProperty
    def teams(self):
        """
        Returns all Team instances related with membership's project and member
        by his/her groups.
        """
        return Team.objects.filter(
            project=self.project,
            group__in=self.member.groups.all()
        )


class Team(models.Model):
    group = models.ForeignKey(Group, verbose_name=_('group'))
    project = models.ForeignKey(Project, verbose_name=_('project'))
    joined_at = models.DateTimeField(_('joined at'), auto_now_add=True)

    objects = TeamManager()

    def __unicode__(self):
        return u"[%s]@%s" % (self.group, self.project)

    class Meta:
        unique_together = ('project', 'group')

    @models.permalink
    def get_absolute_url(self):
        return ('projector_project_teams_edit', (), {
            'username': self.project.author.username,
            'project_slug': self.project.slug,
            'name': self.group.name,
        })

    @models.permalink
    def get_delete_url(self):
        return ('projector_project_teams_delete', (), {
            'username': self.project.author.username,
            'project_slug': self.project.slug,
            'name': self.group.name,
        })

    @LazyProperty
    def perms(self):
        return get_perms(self.group, self.project)

class Milestone(models.Model):
    project = models.ForeignKey(Project, verbose_name=_('project'))
    name = models.CharField(max_length=64)
    slug = AutoSlugField(max_length=64, populate_from='name',
        always_update=True, unique_with='project')
    description = models.TextField()
    author = models.ForeignKey(User, verbose_name=_('author'))
    created_at = models.DateTimeField(_('created at'),
        default=datetime.datetime.now)
    deadline = models.DateField(_('deadline'), default=datetime.date.today() +
        datetime.timedelta(days=10))
            #projector_settings.get_config_value('MILESTONE_DEADLINE_DELTA')))
    date_completed = models.DateField(_('date completed'), null=True,
        blank=True)

    class Meta:
        ordering = ('created_at',)
        verbose_name = _('milestone')
        verbose_name_plural = _('milestones')
        unique_together = ('project', 'name')

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('projector_project_milestone_detail', (), {
            'username': self.project.author.username,
            'project_slug': self.project.slug,
            'milestone_slug': self.slug,
        })

    @models.permalink
    def get_edit_url(self):
        return ('projector_project_milestone_edit', (), {
            'username': self.project.author.username,
            'project_slug': self.project.slug,
            'milestone_slug': self.slug,
        })

    def get_tasks_url(self):
        _url = self.project.get_task_list_url()
        url = _url + '?milestone=%d' % self.pk
        return url

    def get_tasks_count(self):
        return self.task_set.count()

    def get_finished_tasks_count(self):
        finished_tasks = self.task_set\
            .select_related('status')\
            .filter(status__is_resolved=True)
        return finished_tasks.count()

    def get_finished_tasks_count_as_percentage(self):
        finished = self.get_finished_tasks_count()
        all = self.task_set.count()
        if all == 0:
            return 100
        return Decimal(finished) / Decimal(all) * Decimal(100)

    def get_unfinished_tasks_count(self):
        return self.task_set\
            .select_related('status')\
            .filter(status__is_resolved=False)\
            .count()

    def get_unfinished_tasks_count_as_percentage(self):
        return Decimal(100) - self.get_finished_tasks_count_as_percentage()

class TimelineEntry(models.Model):
    project = models.ForeignKey(Project, verbose_name=_('project'),
        editable=False)
    created_at = models.DateTimeField(_('created at'), db_index=True,
        default=datetime.datetime.now)
    author = models.ForeignKey(User, verbose_name=_('author'), null=True,
        blank=True, editable=False)
    action = models.CharField(_('action'), max_length=256,
        help_text=_('Short note on activity, i.e.: "created", "joined" etc.'))
    description = models.TextField(_('description'), null=True, blank=True,
        help_text=_('May be for example a commit messages from single push'))

    class Meta:
        ordering = ('-created_at',)
        get_latest_by = 'created_at'
        verbose_name = _('timeline entry')
        verbose_name_plural = _('timeline entries')

    def __unicode__(self):
        return self.action

    def get_description(self):
        description_date_format = "%Y-%m-%d %H:%m:%s"
        formatted_date = datetime.datetime.strftime(description_date_format,
                self.created_at)
        return "%s by %s at %s" % (self.action, self.author, formatted_date)

class Priority(OrderedDictModel):
    project = models.ForeignKey(Project)
    slug = AutoSlugField(max_length=64, populate_from='name',
        always_update=True, unique_with='project')

    class Meta:
        verbose_name = _('priority level')
        verbose_name_plural = _('priority levels')
        unique_together = ('project', 'name')

class Status(OrderedDictModel):
    project = models.ForeignKey(Project)
    is_resolved = models.BooleanField(verbose_name=_('is resolved'),
        default=False)
    is_initial = models.BooleanField(verbose_name=_('is initial'),
        default=False)
    destinations = models.ManyToManyField('self', verbose_name=_('destinations'),
        through='Transition', symmetrical=False, null=True, blank=True)
    slug = AutoSlugField(max_length=64, populate_from='name',
        always_update=True, unique_with='project')

    def can_change_to(self, new_status):
        """
        Checks if ``Transition`` object with ``source`` set to ``self`` and
        ``destination`` to given ``new_status`` exists.
        """
        try:
            Transition.objects.only('id')\
                .get(source__id=self.id, destination__id=new_status.id)
            return True
        except Transition.DoesNotExist:
            return False

    class Meta:
        verbose_name = _('status')
        verbose_name_plural = _('statuses')
        unique_together = ('project', 'name')
        ordering = ['order']

    def __unicode__(self):
        return self.name

class Transition(models.Model):
    """
    Instances allow to change source Status to destination Status.
    Needed for custom workflows.
    """
    source = models.ForeignKey(Status,
        verbose_name=_('source status'),
        related_name='sources')
    destination = models.ForeignKey(Status,
        verbose_name=_('destination status'))

    class Meta:
        verbose_name = _('transition')
        verbose_name_plural = _('transitions')
        unique_together = ('source', 'destination')

    def __unicode__(self):
        return u'%s->%s' % (self.source, self.destination)

class TaskType(OrderedDictModel):
    project = models.ForeignKey(Project)

    class Meta:
        verbose_name = _('task type')
        verbose_name_plural = _('task types')
        unique_together = ('project', 'name')

class AbstractTask(models.Model):
    """
    This is base abstract class for Task and TaskRevision.
    ``created_at``, ``author`` and ``author_ip`` fields are
    used in a different way - for TaskRevision they work as
    ``edited_at``, ``editor`` and ``editor_ip`` of Task model.
    """
    created_at = models.DateTimeField(_('created at'),
        default=datetime.datetime.now, editable=False)
    author = models.ForeignKey(User, verbose_name=_('author'),
        related_name='created_%(class)s', blank=True)
    author_ip = models.IPAddressField(blank=True)
    revision = models.IntegerField(editable=False, default=0)
    summary = models.CharField(_('summary'), max_length=64)
    description = models.TextField(_('description'))
    status = models.ForeignKey(Status, verbose_name=_('status'))
    priority = models.ForeignKey(Priority, verbose_name=_('priority'))
    type = models.ForeignKey(TaskType, verbose_name=_('task type'))
    owner = models.ForeignKey(User, verbose_name=_('owner'),
        related_name='owned_%(class)s', null=True, blank=True)
    deadline = models.DateField(_('deadline'), null=True, blank=True,
        help_text='YYYY-MM-DD')
    milestone = models.ForeignKey(Milestone, verbose_name=_('milestone'),
        null=True, blank=True)
    component = models.ForeignKey(Component, verbose_name=_('component'))

    def get_status(self):
        return self.status

    def set_status(self, new_status):
        if self.status != new_status:
            self.status = new_status

    class Meta:
        abstract = True

class Task(AbstractTask, Watchable):
    id_pk = models.AutoField(primary_key=True)
    id = models.IntegerField(editable=False)
    project = models.ForeignKey(Project, verbose_name=_('project'))
    edited_at = models.DateTimeField(_('edited at'), auto_now=True)
    editor = models.ForeignKey(User, verbose_name=_('editor'), blank=True,
        null=True)
    editor_ip = models.IPAddressField(blank=True)

    objects = TaskManager()

    class Meta:
        ordering = ('-id',)
        verbose_name = _('task')
        verbose_name_plural = _('tasks')
        unique_together = ('id', 'project')

    def __unicode__(self):
        return u'#%s %s' % (self.id, self.summary)

    class CannotCalucalteIdError(Exception):
        pass

    def _calculate_id(self):
        """
        Sets and returns new id for taks within it's project.
        """
        try:
            self.project # Just check
        except Project.DoesNotExist:
            raise Task.CannotCalucalteIdError("Project is not set for this task")
        if not self.id:
            try:
                latest_task = Task.objects\
                    .filter(project=self.project)\
                    .order_by('-id')[0]
                self.id = latest_task.id + 1
            except IndexError:
                self.id = 1
        logging.debug("Task calulated id is %s" % self.id)
        return self.id

    @models.permalink
    def get_absolute_url(self):
        return ('projector_task_detail', (), {
            'username': self.project.author.username,
            'project_slug': self.project.slug,
            'task_id': self.id,
        })

    @models.permalink
    def get_edit_url(self):
        return ('projector_task_edit', (), {
            'username': self.project.author.username,
            'project_slug': self.project.slug,
            'task_id': self.id,
        })

    @models.permalink
    def get_watch_url(self):
        return ('projector_task_watch', (), {
            'username': self.project.author.username,
            'project_slug': self.project.slug,
            'task_id': self.id,
        })

    @models.permalink
    def get_unwatch_url(self):
        return ('projector_task_unwatch', (), {
            'username': self.project.author.username,
            'project_slug': self.project.slug,
            'task_id': self.id,
        })

    def save(self, *args, **kwargs):
        self._calculate_id()
        if self.pk:
            # Task update
            self.revision += 1
        return super(Task, self).save(*args, **kwargs)

    def _set_comment(self, comment):
        self._comment = comment

    def _get_comment(self):
        return getattr(self, '_comment', None)

    comment = property(_get_comment, _set_comment,
        doc = "If comment is set, clean method won't check if there were "
              "changes made to task itself")

    CHANGESET_FIELDS = (
        'summary',
        'description',
        'status',
        'component',
        'deadline',
        'milestone',
        'owner',
        'priority',
        'type',
    )

    def fetch_old(self):
        return Task.objects.get(pk=self.pk)

    @staticmethod
    def diff(new, old=None):
        """
        Returns differences between old and new task instances,
        as dict. Fields would become keys of returned dict.
        Tuples of old value and new value would be dict's values.
        """
        if old is None:
            # Fetch from database (before commit so it *is* old row)
            old = Task.objects.get(pk=new.pk)
        diff = SortedDict()
        for field in Task.CHANGESET_FIELDS:
            old_val, new_val = getattr(old, field), getattr(new, field)
            if old_val != new_val:
                diff[field] = (old_val, new_val)
        return diff

    def clean(self):
        logging.debug("Validating model... self.comment: %s" % self.comment)
        if self.id and not Task.diff(new=self) and not self.comment:
            raise ValidationError(_("No changes made"))
        return super(Task, self).clean()

    def get_revisions(self, force_query=False):
        """
        Returns TaskRevision objects related to this Task instance.
        Each TaskRevision would have additional attribute ``changes``
        which would containt result of ``Task.diff`` method. For
        first revision changes would be empty dict.
        """
        if force_query or not hasattr(self, '_revisions'):
            revisions = self.taskrevision_set\
                .select_related('type', 'author', 'status', 'editor', 'task',
                    'priority', 'milestone', 'component', 'owner',
                    'task__project')\
                .order_by('revision')
            for i, revision in enumerate(revisions):
                if i==0:
                    revision.changes = {}
                else:
                    revision.changes = Task.diff(revisions[i-1], revision)
            self._revisions = revisions
        return self._revisions

    revisions = property(get_revisions)

    def create_revision(self):
        """
        Creates revision (instance of ``TaskRevision``) for this task. If
        comment has been set, it would be used in revision creation
        process.
        """
        revision_info = dict(
            task = self,
            author = self.editor,
            author_ip = self.editor_ip,
            created_at = self.edited_at,
            revision = self.revision,
            summary = self.summary,
            description = self.description,
            owner = self.owner,
            type = self.type,
            priority = self.priority,
            status = self.status,
            milestone = self.milestone,
            component = self.component,
            deadline = self.deadline,
        )
        if self.comment is not None:
            revision_info['comment'] = self.comment
        revision = TaskRevision.objects.create(**revision_info)
        logging.debug("TaskRevision created: %s" % revision)
        if hasattr(self, '_revisions'):
            self._revisions.append(revision)
        return revision

    def get_long_summary(self):
        raw = self.project.config.task_email_summary_format
        tmpl = string.Template(raw)
        return tmpl.safe_substitute(project=self.project.name,
            id=self.id, summary=self.summary)

    def get_long_content(self):
        """
        Returns content of the task, suitable as email message's body.
        """
        task_url = 'http://%s%s' % (Site.objects.get_current().domain,
            self.get_absolute_url())
        result = render_to_string('projector/project/task/mail.html', {
            'task': self,
            'task_url': task_url,
        })
        return result

    def current_revision(self):
        """
        Returns last TaskRevision (not self) attached to this task. If there
        were no changes made yet, None is returned.
        """
        if self.revision == 0:
            return None
        else:
            return self.taskrevision_set.get(revision=self.revision)

    def notify(self, recipient_list=None):
        """
        Notifies about task's status. If ``recipient_list`` is None, would
        send a note to everyone who watch this task.
        """
        if recipient_list is None:
            recipient_list = self.get_watchers()
        if self.project.is_private():
            if isinstance(recipient_list, QuerySet):
                recipient_list = recipient_list.filter(
                    Q(membership__project=self.project) |
                    Q(project=self.project) |
                    #Q(is_superuser=True) |
                    Q(groups__team__project=self.project))
            else:
                raise TypeError("Currently only QuerySet instances are "
                    "allowed as recipient_list parameter for private "
                    "projects")
        if isinstance(recipient_list, QuerySet):
            recipient_list = recipient_list.values_list('email', flat=True)
        # Be sure not to double recipient
        recipient_list=set(recipient_list)
        mail_info = {
            'subject': self.get_long_summary(),
            'message': self.get_long_content(),
            'from_email': settings.DEFAULT_FROM_EMAIL,
            'recipient_list': [addr for addr in recipient_list],
        }
        send_mail(**mail_info)


class TaskRevision(AbstractTask):
    task = models.ForeignKey(Task)
    comment = models.TextField(_('comment'), max_length=3000,
        null=True, blank=True)

    class Meta:
        ordering = ('task', 'revision',)
        unique_together = ('revision', 'task')

    def __unicode__(self):
        return "#%d %s: Revision %d" % (self.task.id, self.task.summary,
            self.revision)

class UserProfile(RichUserProfile):
    """
    Base user profile class for ``django-projector``.
    Would be abstract if ``AUTH_PROFILE_MODULE`` is not set or doesn't equal
    to ``projector.UserProfile``.
    """
    activation_token = models.CharField(_('activation token'), max_length=32,
        editable=False)
    group = models.OneToOneField(Group, verbose_name=_('group'), null=True,
        blank=True)
    is_team = models.BooleanField(default=False)

    class Meta:
        app_label = 'projector'
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')
        abstract = not using_projector_profile()

    def __unicode__(self):
        return u"<%s's profile>" % self.user


class UserId(models.Model):
    """
    This class would allow to identify users by some kind of id string. Created
    for repository browser - many scm's allow to use username/email combination
    and they may vary. User would be allowed to add such combinations in order
    to be identified by information given from changesets.
    If email is found within given ``raw_id``, user would need to activate this
    UserId - message would be send to the email found.
    """
    user = models.ForeignKey(User, verbose_name = _('user'))
    raw_id = models.CharField(_('Raw ID'), max_length=128, unique=True)
    is_active = models.BooleanField(_('is active'), default=False)
    activation_token = models.CharField(_('activation token'), max_length=32,
        editable=False)

    def __unicode__(self):
        return self.raw_id

    def save(self, *args, **kwargs):
        if self.raw_id:
            user = get_user_from_string(self.raw_id)
            if user:
                raise ValidationError(_("User %s has been identified by this "
                    "value" % user))
        return super(UserId, self).save(*args, **kwargs)

def get_user_from_string(value):
    """
    Returns User instance if given text can be identified or None otherwise.
    First it tries to match with User.username or User.email, next would try
    to match with UserId.raw_id.
    """
    if not value:
        return None
    try:
        return User.objects.get(username=value)
    except User.DoesNotExist:
        pass
    try:
        return User.objects.get(email=value)
    except User.DoesNotExist:
        pass
    try:
        return UserId.objects.get(raw_id=value).user
    except UserId.DoesNotExist:
        pass
    return None

# ================ #
# Signals handlers #
# ================ #

from projector.listeners import start_listening
start_listening()
from projector.actions import actions_start_listening
actions_start_listening()


class Commit(models.Model):
    id = models.CharField(max_length=255)
    project = models.ForeignKey(Project)
    repo = models.ForeignKey(Repository)

    class Meta:
        abstract = True

    @models.permalink
    def get_absolute_url(self):
        return {
            'username': self.project.author.username,
            'project_slug': self.project.slug,
            'revision': self.id,
        }

