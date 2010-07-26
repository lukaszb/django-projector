from django.db import models
from django.db.models import Q
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType

from richtemplates.shortcuts import get_first_or_None

class ProjectManager(models.Manager):

    def for_user(self, user=None):
        """
        Returns queryset of Project instances available
        for given user. If no user is given or user
        is inactive/anonymous, only public projects are
        returned.
        """
        if not user:
            user = AnonymousUser()
        qs = self.get_query_set()
        qset = Q()
        if user.is_active:
            if user.is_superuser:
                pass
            else:
                qset = qset & \
                    Q(public=True) | \
                    Q(public=False, membership__member=user) | \
                    Q(public=False, team__group__in=user.groups.all)
        else:
            qset = qset & Q(public=True)
        qs = qs.filter(qset)\
            .select_related('membership__member')\
            .order_by('name')\
            .distinct()

        return qs

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

