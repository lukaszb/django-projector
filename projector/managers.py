from django.db import models
from django.db.models import Q
from django.contrib.auth.models import AnonymousUser

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
                qset = qset & Q(public=True) | Q(public=False,
                    membership__member=user)
        else:
            qset = qset & Q(public=True)
        qs = qs.filter(qset).select_related('membership__member')
        return qs

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

