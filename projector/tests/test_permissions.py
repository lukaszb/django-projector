import logging

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.test.client import Client
from django.http import HttpResponse

from projector.models import Project
from projector.permissions import ProjectPermission

class ProjectorPermissionTests(TestCase):

    def setUp(self):
        self.client = Client()

        self.admin = User.objects.create_superuser(
            username = 'admin',
            email = 'admin@example.com',
            password = 'admin',
        )
        self.john_doe = User.objects.create_user(
            username = 'john_doe',
            email = 'john_doe@example.com',
            password = 'john_doe',
        )
        self.noperms = User.objects.create_user(
            username = 'noperms',
            email = 'noperms@nodomain.net',
            password = 'noperms',
        )
        # Create projects
        self.public_project = Project.objects.create(
            name = 'public project',
            slug = slugify('public project'),
            author = self.john_doe,
            public = True,
        )
        self.john_project = Project.objects.create(
            name = 'john project',
            slug = slugify('john project'),
            author = self.john_doe,
            public = False,
        )

    def test_public_project(self):
        public_project = Project.objects.filter(public=True)[0]
        for user in User.objects.all():
            check = ProjectPermission(user=user)
            #self.failUnless(
            #    check.has_perm('can_read_repository_project', public_project))
    
    def _assert_url_code(self, url, status_code):
        response = self.client.get(url)
        self.assertTrue(response.status_code == status_code,
            "Status code should be %s, is %s for url '%s'"
            % (status_code, response.status_code, url))

    def _assert_urls_code(self, urls, status_code):
        if not isinstance(urls, tuple):
            raise RuntimeError("Given ``urls`` need to be a tuple")
        for url in urls:
            self._assert_url_code(url, status_code)

    def test_views_anonymous(self):
        self.client.logout()
        urls_200 = (
            reverse('projector_home'),
            reverse('projector_project_list'),
            self.public_project.get_absolute_url(),
            self.public_project.get_members_url(),
            self.public_project.get_task_list_url(),
        )
        self._assert_urls_code(urls_200, 200)
        
        urls_302 = (
            reverse('projector_project_create'),
        )
        self._assert_urls_code(urls_302, 302)

        urls_403 = (
            self.public_project.get_edit_url(),
            self.public_project.get_members_add_url(),
            self.public_project.get_members_manage_url('john_doe'),
            self.public_project.get_create_task_url(),
            self.public_project.get_edit_url(),
            self.public_project.get_milestones_add_url(),
            self.john_project.get_absolute_url(),
            self.john_project.get_edit_url(),
            self.john_project.get_milestones_add_url(),
            self.john_project.get_members_url(),
        )
        self._assert_urls_code(urls_403, 403)
            
    def test_views_logged(self):
        self.client.logout()
        logged = self.client.login(username='noperms', password='noperms')
        urls_200 = (
            reverse('projector_home'),
            reverse('projector_project_list'),
            reverse('projector_project_create'),
            self.public_project.get_absolute_url(),
            self.public_project.get_members_url(),
        )
        self._assert_urls_code(urls_200, 200)

        urls_403 = (
            self.john_project.get_absolute_url(),
            self.john_project.get_edit_url(),
            self.john_project.get_milestones_add_url(),
            self.john_project.get_members_url(),
        )
        self._assert_urls_code(urls_403, 403)
        self.client.logout()
    
    def test_project_details_views(self):
        urls_200 = (
            self.public_project.get_absolute_url(),
        )
        self._assert_urls_code(urls_200, 200)
    
