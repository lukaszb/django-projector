from django.test.client import Client
from django.contrib.auth.models import User

from projector.tests.base import ProjectorTestCase
from projector.models import Project, Milestone


class MilestoneTest(ProjectorTestCase):

    def setUp(self):
        self.client = Client()
        cred = 'milestoner'
        self.user, created = User.objects.get_or_create(
            username = cred,
            email = 'milestoner@example.com',
            is_superuser = True,
            is_active = True)
        self.user.set_password(cred)
        self.user.save()
        self.user._plain_password = cred
        self.project = Project.objects.create_project(
            name = 'milestone-test-project',
            slug = 'milestone-test-project',
            author = self.user,
        )

    def test_name_uniqueness(self):
        self.client.login(username = self.user.username,
            password = self.user._plain_password)

        deadline = u'2012-01-01'

        new_milestone_name = u'milestone-1'
        response = self._get_response(
            url = self.project.get_milestone_add_url())
        instance = response.context['form'].instance

        created_at = instance.created_at.strftime('%Y-%m-%d')

        self._get_response(
            url = self.project.get_milestone_add_url(),
            data = {
                'name': new_milestone_name,
                'description': u'anything',
                'deadline': deadline,
                'created_at': created_at,
            },
            method = 'POST', follow = True)

        self.assertEqual(self.project.milestone_set.count(), 1)

        response = self._get_response(
            url = self.project.get_milestone_add_url(),
            data = {
                'name': new_milestone_name,
                'description': u'anything',
                'deadline': deadline,
                'created_at': created_at,
            },
            method = 'POST', follow = True)

        # Should not be added as it has same name
        self.assertEqual(self.project.milestone_set.count(), 1)
        name_field_errors = response.context['form']._errors['name']
        self.assertTrue(len(name_field_errors) > 0,
            "Milestone with name '%s' for this project already exist "
            "so we shouldn't be able to add new one" % new_milestone_name)

        another_name = u'milestone-2'
        response = self._get_response(
            url = self.project.get_milestone_add_url(),
            data = {
                'name': another_name,
                'description': u'anything',
                'deadline': deadline,
                'created_at': created_at,
            },
            method = 'POST', follow = True)
        # Should not allow to update name of the milestone to one already
        # existing
        milestone = Milestone.objects.get(project = self.project,
            name = another_name)
        response = self._get_response(
            url = milestone.get_edit_url(),
            data = {
                'name': new_milestone_name,
                'description': u'anything',
                'deadline': deadline,
                'created_at': created_at,
            },
            method = 'POST', follow = True)
        name_field_errors = response.context['form']._errors['name']
        self.assertTrue(len(name_field_errors) > 0,
            "Milestone with name '%s' for this project already exist "
            "so we shouldn't be able to change old name '%s' to this one"
            % (new_milestone_name, milestone.name))

