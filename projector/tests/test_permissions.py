from django.test import TestCase
from django.contrib.auth.models import User
#from django.core.urlresolvers import reverse
from django.test.client import Client

from projector.models import Project

class ProjectorPermissionTests(TestCase):

    def runTest(self):
        pass

    def setUp(self):
        self.client = Client()

        self.admin = User.objects.create_superuser(
            username = 'admin',
            email = 'admin@example.com',
            password = 'admin',
        )
        self.admin._plain_password = 'admin'

        self.jack = User.objects.create_user(
            username = 'jack',
            email = 'jack@example.com',
            password = 'jack',
        )
        self.jack._plain_password = 'jack'

        self.joe = User.objects.create_user(
            username = 'joe',
            email = 'joe@example.com',
            password = 'joe',
        )
        self.joe._plain_password = 'joe'

        self.noperms = User.objects.create_user(
            username = 'noperms',
            email = 'noperms@nodomain.net',
            password = 'noperms',
        )
        self.noperms._plain_password = 'noperms'

        # Create projects
        self.public_project = Project.objects.create(
            name = 'Public Project',
            author = self.jack,
            public = True,
        )
        self.private_project = Project.objects.create(
            name = 'Private Project',
            author = self.joe,
            public = False,
        )

    def test_public_project(self):
        for user in (self.admin, self.noperms, self.joe, self.jack):
            client = Client()
            client.login(username=user.username, password=user._plain_password)
            response = client.get(self.public_project.get_absolute_url())
            self.failUnless(response.status_code == 200,
                "User %s doesn't have permission to view public project!"
                % user)
            client.logout()
        # Test anonymous user
        client.logout()
        response = self.client.get(self.public_project.get_absolute_url())
        self.failUnless(response.status_code == 200,
            "User %s doesn't have permission to view public project!"
            % user)

