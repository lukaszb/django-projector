from django.db import models
from django.db.models import Q

class ProjectManager(models.Manager):

    def projects_for_user(self, user=None):
        """
        Returns queryset of Project instances available
        for given user. If no user is given or user
        is inactive/anonymous, only public projects are
        returned.
        """
        qs = self.get_query_set()
        if user.is_active and user.is_superuser:
            return qs
        qset = Q()
        if user.is_active:
            qset = Q(public=True) | Q(public=False, membership__member=user)
        qs = qs.filter(qset)
        ids = set(qs.values_list('pk', flat=True))
        qs = self.get_query_set().select_related('membership__member')
        if ids:
            qs = qs.filter(pk__in=ids)
        return qs

