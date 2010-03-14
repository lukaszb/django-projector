import logging

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
        qset = Q(public=True)
        if user.is_active:
            qset = qset | Q(membership__member=user)
        return qs.filter(qset)


