import logging

from django.test import TestCase
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify

from projector.models import Project
from projector.permissions import ProjectPermission

class ProjectorPermissionTests(TestCase):
    #fixtures = ['tests.json']

    def setUp(self):
        admin = User.objects.create(
            username='admin',
            password='admin',
            is_superuser=True,
            is_staff=True,
        )
        john_doe = User.objects.create(
            username='john_doe',
            password='john_doe',
        )
        Project.objects.create(
            name='public project',
            slug=slugify('public project'),
            author = admin,
        )

    def test_public_project(self):
        logging.info("All users should be able to read repository of "
            "public project.")
        public_project = Project.objects.filter(public=True)[0]
        for user in User.objects.all():
            check = ProjectPermission(user=user)
            check.has_perm('can_read_repository_project', public_project)


