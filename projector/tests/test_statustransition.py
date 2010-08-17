from django.contrib.auth.models import User
from django.test import TestCase
from django.db.models import Q
from django.template.defaultfilters import slugify

from projector.models import Project, Transition, Status

class ProjectorStatusTransition(TestCase):

    def setUp(self):
        name = u'ProjectorStatusTransition'
        self.admin = User.objects.create_superuser(
            username = name,
            email = 'admin@example.com',
            password = 'admin',
        )
        self.project = Project.objects.create_project(
            name=name,
            slug=slugify(name),
            author=self.admin,
        )
        Status.objects.create(name='s1', project=self.project, order=2)
        Status.objects.create(name='s2', project=self.project, order=3)

        Transition.objects.filter(
            Q(source__project=self.project) |
            Q(destination__project=self.project))\
            .delete()

    def test_notransitions(self):
        statuses = self.project.status_set.all()
        for src in statuses:
            for dst in statuses:
                self.assertFalse(src.can_change_to(dst))

    def test_transition(self):
        s1, s2 = self.project.status_set.all()[:2]
        Transition.objects.create(source=s1, destination=s2)
        self.assertTrue(s1.can_change_to(s2))
        self.assertFalse(s2.can_change_to(s1))
        Transition.objects.create(source=s2, destination=s1)
        self.assertTrue(s1.can_change_to(s2))
        self.assertTrue(s2.can_change_to(s1))





