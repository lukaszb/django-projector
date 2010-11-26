from django.db import models
from django.db import IntegrityError
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AnonymousUser, Group
from django.contrib.contenttypes.models import ContentType

from projector.signals import setup_project

from richtemplates.shortcuts import get_first_or_None

class ProjectManager(models.Manager):

    def for_user(self, user=None):
        """
        Returns queryset of :model:`Project` instances available for given
        user. If no user is given or user is inactive/anonymous, only public
        projects are returned.
        """
        if not user:
            user = AnonymousUser()
        qs = self.get_query_set()
        qset = Q()
        if user.is_active:
            qset = qset & \
                Q(public=True) | \
                Q(public=False, membership__member=user) | \
                Q(public=False, team__group__user=user)
        else:
            qset = qset & Q(public=True)
        qs = qs.filter(qset)\
            .select_related('membership__member')\
            .order_by('name')\
            .distinct()

        return qs

    def for_member(self, user, requested_by):
        """
        Returns queryset of :model:`Project` instances which given ``user`` is
        member of with exclusion of those projects which ``requested_by`` user
        cannot see (i.e. are private and ``requested_by`` is not member of).
        """
        qs = self.for_user(requested_by)
        qset = Q()

        if user.is_anonymous():
            raise ValueError("Only requeted_by parameter may be anonymous")

        qset = qset & \
            Q(membership__member=user) | \
            Q(team__group__user=user)

        qs = qs.filter(qset)\
            .select_related('membership__member')\
            .order_by('name')\
            .distinct()

        return qs

    def create_project(self, vcs_alias=None, workflow=None, *args, **kwargs):
        """
        Creates new project and call it's setup function by sending
        :signal:`setup_project` signal.
        """
        instance = self.create(*args, **kwargs)
        setup_project.send(sender=self.model, instance=instance,
            vcs_alias=vcs_alias, workflow=workflow)
        return instance

    def get_actions(self, project, include_private=False):
        from actstream.models import Action
        from projector.models import Project
        ctype = ContentType.objects.get_for_model(Project)
        q1 = Q(action_object_content_type=ctype, action_object_object_id=project.pk)
        q2 = Q(target_content_type=ctype, target_object_id=project.pk)
        qset = q1 | q2
        queryset = Action.objects\
            .filter(qset)\
            .order_by('-timestamp')
        if not include_private:
            queryset = queryset.filter(public=True)
        return queryset


class TaskManager(models.Manager):

    def get_for_project(self, project):
        """
        Returns Task instance with default values set related to given
        project.
        """
        from projector.models import Task
        status = get_first_or_None(
            project.status_set.filter(is_initial=True))
        type = get_first_or_None(project.tasktype_set)
        priority = get_first_or_None(project.priority_set)
        component = get_first_or_None(project.component_set)

        task = Task(
            project = project,
            status = status,
            type = type,
            priority = priority,
            component = component,
        )
        return task


class TeamManager(models.Manager):

    def for_user(self, user=None):
        """
        Returns queryset of Team instances of groups for given user.
        """
        if not user:
            user = AnonymousUser()
        queryset = self.get_query_set()
        queryset = queryset.filter(group__user=user)
        return queryset

    def convert_from_user(self, user):
        """
        Converts ``User`` instance into ``Team`` instance. It won't delete user,
        his or her profile would simply get ``team`` attribute set to newly
        created ``Team`` and ``is_team`` attribute would be set to ``True``.
        """
        from projector.models import Project
        if not user.is_active or user.is_anonymous():
            raise ValidationError("Cannot conver anonymous or inactive user")
        elif user.is_superuser or user.is_staff:
            raise ValidationError("Cannot convert staff member or superuser")
        try:
            group = Group.objects.create(name=user.username)
            profile = user.get_profile()
            profile.is_team = True
            profile.group = group
            profile.save()
            user.groups.add(group)
            for project in Project.objects.filter(author=user):
                self.create(project = project, group = group)
            return group
        except IntegrityError:
            raise ValidationError("Cannot convert user if a group with same "
                "name already exist")


class WatchedItemManager(models.Manager):

    def projects_for_user(self, user):
        """
        Returns Project instances watched by user.
        """
        from projector.models import Project
        qs = self.get_query_set().filter(
            content_type = ContentType.objects.get_for_model(Project),
            user = user,
        )
        return qs

    def task_for_user(self, user):
        """
        Returns Task instances watched by user.
        """
        from projector.models import Task
        qs = self.get_query_set().filter(
            content_type = ContentType.objects.get_for_model(Task),
            user = user,
        )
        return qs

