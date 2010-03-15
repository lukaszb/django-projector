import os
import pprint
import datetime
import logging
import mercurial
import mercurial.ui
import mercurial.hg

from decimal import Decimal

from django.conf import settings
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
from projector.utils import abspath
from projector.settings import HG_ROOT_DIR, BANNED_PROJECT_NAMES
from projector.exceptions import ProjectorError
from projector.managers import ProjectManager
from tagging.fields import TagField

class DictModel(models.Model):
    #id = models.IntegerField('ID', primary_key=True)
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

class Project(models.Model):
    name = models.CharField(_('name'), max_length=64, unique=True)
    category = models.ForeignKey(ProjectCategory, verbose_name=_('category'), null=True, blank=True)
    description = models.TextField(_('description'), null=True, blank=True)
    slug = models.SlugField(unique=True)
    home_page_url = models.URLField(_("home page url "), null=True, blank=True, verify_exists=False)
    repository_url = models.CharField(_('repository url'), max_length=256, null=True, blank=True)
    active = models.BooleanField(_('active'), default=True)
    public = models.BooleanField(_('public'), default=True)
    members = models.ManyToManyField(User, verbose_name=_('members'), through="Membership")
    author = models.ForeignKey(User, name=_('author'), related_name='created_projects')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    modified_at = models.DateTimeField(_('modified at'), auto_now=True)
    outdated = models.BooleanField(_('outdated'), default=False)
    #tags = TagField()

    objects = ProjectManager()
    
    class WrongProjectNameError(ProjectorError): pass

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
        return ('projector_project_members_add', (), {'project_slug': self.slug })

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
    def get_milestones_add_url(self):
        return ('projector_project_milestones_add', (),
            {'project_slug': self.slug })
    
    @models.permalink
    def get_browse_repo_url(self):
        return ('projector_project_browse_repository', (), {
            'project_slug': self.slug,
            'rel_repo_url': '/',
        })
    
    def get_repo_path(self):
        repo_path = abspath(HG_ROOT_DIR, self.slug)
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

    def save(self, *args, **kwargs):
        if self.name.lower() in BANNED_PROJECT_NAMES:
            raise WrongProjectNameError("Project's '%r' cannot be used - it "
                "is one of the banned names:\n%s"
                % (self.name, pprint.pformat(BANNED_PROJECT_NAMES)))
        super(Project, self).save(*args, **kwargs)
        self.set_author_permissions()

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
        from projector.permissions import ProjectPermission, get_or_create_permisson
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

class ProjectComponent(models.Model):
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
    #permissions = models.ManyToManyField(Permission, verbose_name=_('permissions'))

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
    description = models.TextField()
    author = models.ForeignKey(User, verbose_name=_('author'))
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    deadline = models.DateField(_('deadline'), default=datetime.date.today() +
            datetime.timedelta(days=60))
    date_completed = models.DateField(_('date completed'), null=True, blank=True)
    
    class Meta:
        ordering = ('created_at',)
        verbose_name = _('milestone')
        verbose_name_plural = _('milestones')
        unique_together = ('project', 'name')

    def __unicode__(self):
        return self.name
    
    def get_finished_tasks_count(self):
        finished_tasks = self.task_set\
            .select_related('status')\
            .filter(status__is_resolved=True)
        return finished_tasks.count()

    def get_finished_tasks_count_as_percentage(self):
        finished = self.get_finished_tasks_count()
        all = self.task_set.count()
        return Decimal(finished) / Decimal(all) * Decimal(100)

    def get_unfinished_tasks_count_as_percentage(self):
        return Decimal(100) - self.get_finished_tasks_count_as_percentage()

class TimelineEntry(models.Model):
    project = models.ForeignKey(Project, verbose_name=_('project'), editable=False)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True, editable=False)
    user = models.ForeignKey(User, verbose_name=_('user'), null=True, blank=True, editable=False)
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
    is_resolved = models.BooleanField(verbose_name=_('is resolved'), default=False)
    is_task_action = models.BooleanField(verbose_name=_('is task action'), default=False)
    
    class Meta:
        verbose_name = _('status')
        verbose_name_plural = _('statuses')
        unique_together = ('project', 'name')
    
    def __unicode__(self):
        return self.name

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
    created_at = models.DateTimeField(_('created at'), default=datetime.datetime.now, editable=False)
    author = models.ForeignKey(User, verbose_name=_('author'), related_name='created_%(class)s', blank=True)
    author_ip = models.IPAddressField(blank=True)
    revision = models.IntegerField(editable=False, default=0)
    summary = models.CharField(_('summary'), max_length=64)
    description = models.TextField(_('description'))
    status = models.ForeignKey(Status, verbose_name=_('status'))
    priority = models.ForeignKey(Priority, verbose_name=_('priority'))
    type = models.ForeignKey(TaskType, verbose_name=_('task type'))
    owner = models.ForeignKey(User, verbose_name=_('owner'), related_name='owned_%(class)s')
    deadline = models.DateField(_('deadline'), null=True, blank=True, help_text='YYYY-MM-DD')
    milestone = models.ForeignKey(Milestone, verbose_name=_('milestone'), null=True, blank=True)
    component = models.ForeignKey(ProjectComponent, verbose_name=_('component'))

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

    def make_revision(self, old=None, comment=None, commit=True):
        """
        Once done completely via signals but since we need to
        leave comment as optional attribute we need separete
        logic fragment for this.
        ``old`` parameter is optional as not passing it would
        force the method to fetch original Task object directly
        from database.
        """
        if old is None:
            old = self.fetch_old()
        diff = Task.diff(old, self)
        revision_info = dict(
            task = old,
            author = old.editor,
            author_ip = old.editor_ip,
            created_at = old.edited_at,
            revision = old.revision,
            summary = old.summary,
            description = old.description,
            owner = old.owner,
            type = old.type,
            priority = old.priority,
            status = old.status,
            milestone = old.milestone,
            component = old.component,
        )
        if comment:
            revision_info['comment'] = comment
        if commit:
            revision = TaskRevision.objects.create(**revision_info)
        else:
            revision = TaskRevision(**revision_info)
        return revision

    def add_comment_to_current_revision(self, comment):
        """
        Adds given ``comment`` to the current TaskRevision (last revisioned).
        """
        self.taskrevision_set\
            .filter(revision=self.revision)\
            .update(comment=comment)

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

class TaskRevision(AbstractTask):
    task = models.ForeignKey(Task)
    comment = models.TextField(_('comment'), max_length=3000,
        null=True, blank=True)

    class Meta:
        ordering = ('task', 'revision',)
        unique_together = ('revision', 'task')

    def __unicode__(self):
        return _("Revision ") + str(self.revision)

@signals.pre_save(sender=Task)
def update_task_handler_pre(instance, **kwargs):
    #logging.debug("Signal pre_save\nInstance: %s\nkwargs:%s"
    #    % (instance, pprint.pformat(kwargs)))
    #logging.debug("Instance's dict:\n%s" % pprint.pformat(instance.__dict__))
    pass

@signals.post_save(sender=Task)
def update_task_handler(instance, **kwargs):
    """
    Called every time Task.save method is called.
    """
    revision = TaskRevision.objects.create(
        task = instance,
        author = instance.editor,
        author_ip = instance.editor_ip,
        created_at = instance.edited_at,
        revision = instance.revision,
        summary = instance.summary,
        description = instance.description,
        owner = instance.owner,
        type = instance.type,
        priority = instance.priority,
        status = instance.status,
        milestone = instance.milestone,
        component = instance.component,
    )
    logging.debug("TaskRevision created: %s" % revision)

# ================= #
# User profile part #
# ================= #

# If projector is kind of main application in your project
# it's build-in user profile could be used as it provides
# some nice user buffs
# TODO: Well, at least it should provide buffs, but none of them exists now...

class UserProfile(models.Model):
    user = models.ForeignKey('auth.User', verbose_name=_('user'), unique=True)
    activation_token = models.CharField(_('activation_token'), max_length=32)

    class Meta:
        app_label = 'auth'
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')

    def __unicode__(self):
        return u"<%s's profile>" % self.user

@signals.post_save(sender=User)
def request_new_profile(sender, instance, **kwargs):
    """
    Creation of profile for new users
    """
    profile, created = UserProfile.objects.get_or_create(
        user=instance,
    )
    if created is True:
        logging.debug("Creating profile for %s ..." % instance)
        profile.activation_token = default_token_generator.make_token(instance)
        profile.save()
        logging.debug("Created profile's id: %s" % profile.id)

new_components = (
    {
        'name': u'Global',
    },
)

new_task_types = (
    {
        'name': u'Task',
        'order': 1,
    },
    {
        'name': u'Defect',
        'order': 2,
    },
    {
        'name': u'New feature',
        'order': 3,
    },
    {
        'name': u'Proposal',
        'order': 4,
    },
    {
        'name': u'Blocker',
        'order': 5,
    },
)

new_priorities = (
    {
        'name': u'Blocker',
        'order': 1,
    },
    {
        'name': u'Critical',
        'order': 2,
    },
    {
        'name': u'Major',
        'order': 3,
    },
    {
        'name': u'Minor',
        'order': 4,
    },
)

new_statuses = (
    {
        'name': u'New',
        'order': 1,
        'is_resolved': False,
        'is_task_action': False,
    },
    {
        'name': u'Assigned',
        'order': 2,
        'is_resolved': False,
        'is_task_action': False,
    },
    {
        'name': u'Need fix',
        'order': 3,
        'is_resolved': False,
        'is_task_action': False,
    },
    {
        'name': u'Need feedback',
        'order': 4,
        'is_resolved': False,
        'is_task_action': False,
    },
    {
        'name': u'Need unittest',
        'order': 5,
        'is_resolved': False,
        'is_task_action': False,
    },
    {
        'name': u'Fixed',
        'order': 6,
        'is_resolved': True,
        'is_task_action': False,
    },
    {
        'name': u'Closed',
        'order': 7,
        'is_resolved': True,
        'is_task_action': False,
    },
    {
        'name': u'Wrong',
        'order': 8,
        'is_resolved': True,
        'is_task_action': False,
    },
)

@signals.pre_save(sender=Project)
def project_creation_listener(instance, **kwargs):
    if instance.pk is not None:
        return
    if HG_ROOT_DIR:
        repo_path = instance.get_repo_path()
        logging.info("Creating new mercurial repository at %s" % repo_path)
        if os.path.exists(repo_path):
            logging.warn("Project '%s': cannot create repository "
                "as path '%s' already exists" % (instance, repo_path))
        else:
            repo = mercurial.hg.repository(mercurial.ui.ui(), repo_path,
                create=True)
        instance.repository_url = repo_path
    else:
        logging.debug("PROJECTOR_HG_ROOT_DIR is not set so we do NOT "
            "create repository to this project.")

@signals.post_save(sender=Project)
def new_project_handler(instance, **kwargs):
    if kwargs['created'] is True:
        logging.debug("Project '%s': new project handler." % instance)
        member = Membership.objects.create(project=instance, member=instance.author)
        component, created = ProjectComponent.objects\
            .get_or_create(project=instance, name=u'Global')
        
        if created:
            logging.debug("Created standard 'Global' component for project %s"
                % instance.name)
        for component_info in new_components:
            component, created = ProjectComponent.objects\
                .get_or_create(
                    project = instance,
                    **component_info)
            if created:
                logging.debug("For project '%s' new component '%s' was craeted"
                    % (component.project, component))
        for task_type_info in new_task_types:
            task, created = TaskType.objects\
                .get_or_create(
                    project = instance,
                    **task_type_info)
            if created:
                logging.debug("For project '%s' new task type '%s' was craeted"
                    % (task.project, task))
        for priority_info in new_priorities:
            priority, created = Priority.objects\
                .get_or_create(
                    project = instance,
                    **priority_info)
            if created:
                logging.debug("For project '%s' new priority '%s' was created."
                    % (priority.project, priority))
        for status_info in new_statuses:
            status, created = Status.objects\
                .get_or_create(
                    project = instance,
                    **status_info)
            if created:
                logging.debug("For project '%s' new status '%s' was created."
                    % (status.project, status))
    else:
        logging.debug("Project '%s': update handler." % instance)

