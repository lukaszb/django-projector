import logging

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.test.client import Client

from projector.models import Project
from projector.permissions import ProjectPermission

class ProjectorPermissionTests(TestCase):

    def setUp(self):
        self.client = Client()

        self.admin = User.objects.create(
            username = 'admin',
            password = 'admin',
            is_superuser = True,
            is_staff = True,
        )
        self.john_doe = User.objects.create(
            username = 'john_doe',
            password = 'john_doe',
        )
        self.public_project = Project.objects.create(
            name = 'public project',
            slug = slugify('public project'),
            author = self.john_doe,
        )

    def test_public_project(self):
        public_project = Project.objects.filter(public=True)[0]
        for user in User.objects.all():
            check = ProjectPermission(user=user)
            check.has_perm('can_read_repository_project', public_project)

    def test_basic_views(self):
        self.client.logout()
        urls_200 = (
            reverse('projector_home'),
            reverse('projector_project_list'),
        )
        for url in urls_200:
            response = self.client.get(url)
            self.assertTrue(response.status_code, 200)

    def test_project_details_views(self):
        responses_200 = (
            self.client.get(self.public_project.get_absolute_url()),
        )

        for response in responses_200:
            self.assertTrue(response.status_code == 200)


