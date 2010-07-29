from django.test.client import Client
from django.contrib.auth.models import User

from projector.tests.base import ProjectorTestCase
from projector.models import Project
from projector.settings import get_workflow

statuses = get_workflow().statuses

class StatusTest(ProjectorTestCase):

    def setUp(self):
        self.client = Client()
        cred = 'statuser'
        self.user, created = User.objects.get_or_create(
            username = cred,
            email = 'statuser@example.com',
            is_superuser = True,
            is_active = True)
        self.user.set_password(cred)
        self.user.save()
        self.user._plain_password = cred
        self.project, created = Project.objects.get_or_create(
            name = 'status-test-project',
            slug = 'status-test-project',
            author = self.user,
        )

    def test_name_uniqueness(self):
        self.client.login(username = self.user.username,
            password = self.user._plain_password)

        order = len(statuses) + 1
        new_status_name = u'status-1'
        self._get_response(
            url = self.project.get_workflow_add_status_url(),
            data = {'name': new_status_name, 'order': unicode(order)},
            method = 'POST', follow = True)
        order += 1

        self.assertEqual(self.project.status_set.count(), len(statuses) + 1)

        self._get_response(
            url = self.project.get_workflow_add_status_url(),
            data = {'name': new_status_name, 'order': unicode(order)},
            method = 'POST', follow = True)

        # TODO: Need to test editing statuses' names

