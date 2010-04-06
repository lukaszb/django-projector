import os
import pprint
import datetime
import logging
import mercurial
import mercurial.ui
import mercurial.hg

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User, Group
from django.contrib.auth.tokens import default_token_generator
from django.utils.safestring import mark_safe
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.utils.datastructures import SortedDict
from django.template.defaultfilters import slugify

from annoying.decorators import signals
from authority.models import Permission
from projector.conf import default_workflow
from projector.utils import abspath, using_projector_profile
from projector import settings as projector_settings
from projector.exceptions import ProjectorError
from projector.managers import ProjectManager
from richtemplates.forms import RichSkinChoiceField
from richtemplates.utils import get_user_profile_model
from tagging.fields import TagField

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
            'project_category_slug' : self.slug })

def validate_project_name(name):
    """
    Checks if this project name may be used.
    """
    if name.lower() in projector_settings.BANNED_PROJECT_NAMES:
        raise ValidationError(_("This name is restricted"))

class Project(models.Model):
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
    author = models.ForeignKey(User, name=_('author'),
        related_name='created_projects')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(_('modified at'), auto_now=True)
    outdated = models.BooleanField(_('outdated'), default=False)

    objects = ProjectManager()

    class Meta:
        verbose_name = _('project')
        verbose_name_plural = _('projects')
        ordering = ['name']
        permissions = (
            ('can_read_repository', 'Can read repository'),
            ('can_write_to_repository', 'Can write to repository'),
            ('can_change_description', 'Can change description'),
            ('can_change_category', 'Can change category'),
            ('can_add_task', 'Can add task'),
            ('can_change_task', 'Can change task'),
            ('can_delete_task', 'Can delete task'),
            ('can_add_member', 'Can add member'),
            ('can_change_member', 'Can change member'),
            ('can_delete_member', 'Can delete member'),
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
        super(Project, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return ('projector_project_details', (), {'project_slug' : self.slug })

    @models.permalink
    def get_edit_url(self):
        return ('projector_project_edit', (), {'project_slug' : self.slug })

    @models.permalink
    def get_members_url(self):
        return ('projector_project_members', (), {'project_slug' : self.slug })

    @models.permalink
    def get_members_add_url(self):
        return ('projector_project_members_add', (),
            {'project_slug': self.slug })

    @models.permalink
    def get_members_manage_url(self, username):
        return ('projector_project_members_manage', (),
            {'project_slug': self.slug, 'username': username})

    @models.permalink
    def get_create_task_url(self):
        return ('projector_task_create', (), {'project_slug': self.slug})

    @models.permalink
    def get_task_list_url(self):
        return ('projector_task_list', (), {'project_slug': self.slug})

    @models.permalink
    def get_milestones_url(self):
        return ('projector_project_milestones', (),
            {'project_slug': self.slug })

    @models.permalink
    def get_milestones_add_url(self):
        return ('projector_project_milestones_add', (),
            {'project_slug': self.slug })

    @models.permalink
    def get_workflow_url(self):
        return ('projector_project_workflow_detail', (),
            {'project_slug': self.slug })

    @models.permalink
    def get_workflow_edit_url(self):
        return ('projector_project_workflow_edit', (),
            {'project_slug': self.slug })

    @models.permalink
    def get_workflow_add_status_url(self):
        return ('projector_project_workflow_add_status', (),
            {'project_slug': self.slug })

    @models.permalink
    def get_browse_repo_url(self):
        return ('projector_project_browse_repository', (), {
            'project_slug': self.slug,
            'rel_repo_url': '',
        })

    @models.permalink
    def get_changesets_url(self):
        return ('projector_project_changesets', (),
            {'project_slug': self.slug})

    def get_task(self, id):
        queryset = Task.objects.filter(project=self)
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
        from django.contrib.sites.models import Site
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
        from projector.permissions import ProjectPermission
        from projector.permissions import get_or_create_permisson
        available_permissions = ProjectPermission.get_local_checks()

        perms = Permission.objects.for_user(self.author, self)
        perms_set = itertools.chain(perms.values_list('codename'))
        check = ProjectPermission(self.author)
        for perm in available_permissions:
            if not perm in perms_set:
                logging.debug("Project '%s': adding '%s' permission for user "
                    "'%s'" % (self, perm, self.author))
                get_or_create_permisson(
                    user = self.author,
                    project = self,
                    codename = perm)

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

        membership = Membership.objects.create(project=self,
            member=self.author)
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

class Component(models.Model):
    project = models.ForeignKey(Project)
    name = models.CharField(max_length=64)
    description = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = _('component')
        verbose_name_plural = _('components')
        unique_together = ('project', 'name')
        ordering = ('name',)

    def __unicode__(self):
        return self.name

class Membership(models.Model):
    member = models.ForeignKey(User, verbose_name=_('member'))
    joined_at = models.DateTimeField(_('joined at'), auto_now_add=True)
    project = models.ForeignKey(Project, verbose_name=_('project'))

    def __unicode__(self):
        return u"%s@%s" % (self.member, self.project)

    class Meta:
        unique_together = ('project', 'member')

    @models.permalink
    def get_absolute_url(self):
        return ('projector_project_members_manage', (), {
            'project_slug': self.project.slug,
            'username': self.member.username,
        })

class Milestone(models.Model):
    project = models.ForeignKey(Project, verbose_name=_('project'))
    name = models.CharField(max_length=64)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    author = models.ForeignKey(User, verbose_name=_('author'))
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    deadline = models.DateField(_('deadline'), default=datetime.date.today() +
        datetime.timedelta(days=projector_settings.DEFAULT_DEADLINE_DELTA))
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
            'project_slug': self.project.slug,
            'milestone_slug': self.slug,
        })

    @models.permalink
    def get_edit_url(self):
        return ('projector_project_milestone_edit', (), {
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
    created_at = models.DateTimeField(_('created at'), auto_now_add=True,
        editable=False)
    user = models.ForeignKey(User, verbose_name=_('user'), null=True,
        blank=True, editable=False)
    action = models.CharField(_('action'), max_length=256)

    class Meta:
        ordering = ('-id',)
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

class Task(AbstractTask):
    id_pk = models.AutoField(primary_key=True)
    id = models.IntegerField(editable=False)
    project = models.ForeignKey(Project, verbose_name=_('project'))
    edited_at = models.DateTimeField(_('edited at'), auto_now=True)
    editor = models.ForeignKey(User, verbose_name=_('editor'), blank=True, null=True)
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
            'project_slug': self.project.slug,
            'task_id' : self.id,
        })

    @models.permalink
    def get_edit_url(self):
        return ('projector_task_edit', (), {
            'project_slug': self.project.slug,
            'task_id' : self.id,
        })

    def save(self, *args, **kwargs):
        self._calculate_id()
        #if not self.pk:
        #    self.status= Status.objects.get(id=1)
        #else:
        if self.pk:
            # Task update
            self.revision += 1
        return super(Task, self).save(*args, **kwargs)

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

    def create_revision(self, comment=None):
        """
        Creates revision (instance of ``TaskRevision``) for this task.
        """
        logging.debug("TEMP: Going to create revision for task %s" % self)
        logging.debug("TEMP: task current status is %s" % self.status)
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
        if comment is not None:
            revision_info['comment'] = comment
        revision = TaskRevision.objects.create(**revision_info)
        logging.debug("TaskRevision created: %s" % revision)
        if hasattr(self, '_revisions'):
            self._revisions.append(revision)
        return revision

class TaskRevision(AbstractTask):
    task = models.ForeignKey(Task)
    comment = models.TextField(_('comment'), max_length=3000,
        null=True, blank=True)

    class Meta:
        ordering = ('task', 'revision',)
        unique_together = ('revision', 'task')

    def __unicode__(self):
        return _("Revision ") + str(self.revision)

# ==================== #
# Signals and handlers #
# ==================== #

@signals.post_save(sender=User)
def request_new_profile(sender, instance, **kwargs):
    """
    Creation of profile for new users
    """
    _UserProfile = get_user_profile_model()
    if _UserProfile is None:
        return
    profile, created = _UserProfile.objects.get_or_create(
        user=instance,
    )
    if created is True:
        logging.debug("Creating profile for %s ..." % instance)
        profile.activation_token = default_token_generator.make_token(instance)
        profile.save()
        logging.debug("Created profile's id: %s" % profile.id)

@signals.post_save(sender=Project)
def project_created_listener(instance, **kwargs):
    if not kwargs.get('created', False):
        return
    if projector_settings.PROJECTS_ROOT_DIR:
        repo_path = instance._get_repo_path()
        logging.info("Creating new mercurial repository at %s" % repo_path)
        if os.path.exists(repo_path):
            logging.warn("Project '%s': cannot create repository "
                "as path '%s' already exists" % (instance, repo_path))
        else:
            repo = mercurial.hg.repository(mercurial.ui.ui(), repo_path,
                create=True)
    else:
        logging.debug("PROJECTOR_PROJECTS_ROOT_DIR is not set so we do NOT "
            "create repository to this project.")

