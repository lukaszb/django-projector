import os
import string
import datetime
import logging

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string
from django.contrib.auth.models import User, Group, AnonymousUser, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.datastructures import SortedDict
from django.contrib.sites.models import Site

from guardian.shortcuts import assign, get_perms, get_perms_for_model

from autoslug import AutoSlugField

from projector.conf import default_workflow
from projector.exceptions import ConfigAlreadyExist
from projector.utils import abspath, using_projector_profile
from projector.utils.lazy import LazyProperty
from projector import settings as projector_settings
from projector.settings import get_config_value
from projector.managers import ProjectManager, TeamManager, WatchedItemManager

from vcs.web.simplevcs.models import Repository

from richtemplates.models import UserProfile as RichUserProfile


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
        return ('projector_project_category_details', (), {
            'username': self.project.author.username,
            'project_category_slug' : self.slug,
        })

def validate_project_name(name):
    """
    Checks if this project name may be used.
    """
    if name.lower() in projector_settings.BANNED_PROJECT_NAMES:
        raise ValidationError(_("This name is restricted"))

class Project(models.Model, Watchable):
    name = models.CharField(_('name'), max_length=64, unique=True,
        validators=[validate_project_name])
    category = models.ForeignKey(ProjectCategory, verbose_name=_('category'),
        null=True, blank=True)
    description = models.TextField(_('description'), null=True, blank=True)
    slug = models.SlugField(unique=True, validators=[validate_project_name])
    home_page_url = models.URLField(_("home page url "), null=True, blank=True,
        verify_exists=False)
    active = models.BooleanField(_('active'), default=True)
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
    fork = models.ForeignKey('self', null=True, blank=True,
        editable=False)

    objects = ProjectManager()

    class Meta:
        verbose_name = _('project')
        verbose_name_plural = _('projects')
        ordering = ['name']
        get_latest_by = 'created_at'
        permissions = (
            ('view_project', 'Can view project'),
            ('change_config_project', 'Can change config'),
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

    def _set_author_permissions(self):
        """
        Creates all permissions for project's author.
        """
        perms = [p.codename for p in get_perms_for_model(Project)
            if p.codename != 'add_project']
        for perm in perms:
            assign(perm, self.author, self)

    def is_public(self):
        return self.public

    def is_private(self):
        return not self.public

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        self.full_clean()
        project = super(Project, self).save(*args, **kwargs)
        # Add necessary permissions for author - we need to do this
        # *NOT* asynchronousely as isntant redirect after project creation
        # may cause it's author not to be able to see project page
        self._set_author_permissions()
        return project

    @models.permalink
    def get_absolute_url(self):
        return ('projector_project_details', (), {
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
    def get_milestones_add_url(self):
        return ('projector_project_milestones_add', (), {
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
        Returns directory containing all files related to this project.
        """
        homedir = abspath(projector_settings.PROJECTS_ROOT_DIR, str(self.id))
        if not homedir.endswith('/'):
            homedir += '/'
        if os.path.exists(projector_settings.PROJECTS_ROOT_DIR) and \
            not os.path.exists(homedir):
            os.mkdir(homedir)
            logging.debug("Project '%s': Created homedir at %s"
                % (self, homedir))
        return homedir

    def _get_repo_path(self):
        repo_path = abspath(self._get_homedir(), 'hg')
        return repo_path

    def get_repo_url(self):
        """
        Returns full url of the project (with domain based on
        django sites framework).
        """
        current_site = Site.objects.get_current()
        if settings.DEBUG:
            prefix = 'http://'
        else:
            prefix = 'https://'
        return ''.join((prefix, current_site.domain, self.get_absolute_url()))

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
        Creates all available permissions for the author of
        the project. Should be called every time project is
        saved to ensure that at any given time project's author
        has all permissions for the project.
        """
        if self.author.is_superuser:
            # we don't need to add permissions for superuser
            # as superusers has all permissions
            return
        import itertools
        available_permissions = set([p.codename for p in
            get_perms_for_model(Project) if p.codename != 'add_project'])

        perms = get_perms(self.author, self)
        perms_set = set(itertools.chain(perms.values_list('codename')))
        for perm in available_permissions:
            if not perm in perms_set:
                logging.debug("Project '%s': adding '%s' permission for user "
                    "'%s'" % (self, perm, self.author))
                assign(perm, self.author, self)

    def create_workflow(self, workflow=default_workflow):
        """
        Creates default workflow for the project. We need to create initial
        member (author) and objects required to work on issues (components,
        types, statuses with their transitions).

        :param workflow: python object defining tuples of dicts with
          information on project *metadata*; by default module
          ``projector.conf.default_workflow`` is used - take a look at it if
          you want to use your own object
        """

        Membership.objects.create(project=self, member=self.author)
        self.set_author_permissions()

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

    def get_config(self):
        """
        Returns Config for this project.
        """
        return Config.objects.get(project=self)
    config = property(get_config)

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
        help_text = _(''.join((
            'Every milestone has its deadline and this number specifies ',
            'how many days would be given by default. It may be set to ',
            'any date during milestone creation process though.',
        ))),
        )

    def __unicode__(self):
        return u'<Config for %s>' % self.project

    @staticmethod
    def create_for_project(project):
        """
        Creates default configuration for given project.
        """
        if project.config_set.count() > 0:
            raise ConfigAlreadyExist("Project %s with id %d has already "
                "related configuration" % (project, project.id))
        config = Config.objects.create(
            project = project,
            editor = project.author,
        )
        return config

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
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    deadline = models.DateField(_('deadline'), default=datetime.date.today() +
        datetime.timedelta(days=10))
            #projector_settings.get_config_value('MILESTONE_DEADLINE_DELTA')))
    date_completed = models.DateField(_('date completed'), null=True,
        blank=True)

    class Meta:
        ordering = ('created_at',)
        verbose_name = _('milestone')
        verbose_name_plural = _('milestones')
        #unique_together = ('project', 'slug')

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
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    user = models.ForeignKey(User, verbose_name=_('user'), null=True,
        blank=True, editable=False)
    action = models.CharField(_('action'), max_length=256,
        help_text=_('Short note on activity, i.e.: commit message'))

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
        logging.debug("Task's _calculate_id method called")
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
        return ('projector_task_details', (), {
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
        raw = get_config_value('TASK_EMAIL_SUBJECT_SUMMARY_FORMAT')
        tmpl = string.Template(raw)
        return tmpl.safe_substitute(project=self.project.name,
            id=self.id, summary=self.summary)

    def get_long_content(self):
        """
        Returns content of the task, suitable as email message's body.
        """
        task_url = 'http://%s/%s' % (Site.objects.get_current().domain,
            self.get_absolute_url())
        result = render_to_string('projector/task/mail.html', {
            'task': self,
            'task_url': task_url,
        })
        return result

    def get_last_revision(self):
        """
        Returns last TaskRevision (not self) attached to this task. If there
        were no changes made yet, None is returned.
        """
        if self.revision == 0:
            return None
        else:
            return self.taskrevision_set.get(revision=self.revision-1)

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
    with ``projector.UserProfile``.
    """
    activation_token = models.CharField(_('activation_token'), max_length=32,
        editable=False)

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
    activation_token = models.CharField(_('activation_token'), max_length=32,
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

