from django.test.client import Client
from django.contrib.auth.models import User

from projector.tests.base import ProjectorTestCase
from projector.models import Project
from projector.utils import str2obj
from projector.settings import get_config_value

statuses = str2obj(get_config_value('DEFAULT_PROJECT_WORKFLOW')).statuses

class StatusTest(ProjectorTestCase):

    def setUp(self):
        self.client = Client()
        cred = 'statuser'
        self.user = User.objects.create(
            username = cred,
            email = 'statuser@example.com',
            is_superuser = True,
            is_active = True)
        self.user.set_password(cred)
        self.user.save()
        self.user._plain_password = cred
        self.project = Project.objects.create_project(
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

