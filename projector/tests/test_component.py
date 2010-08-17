from django.test.client import Client
from django.contrib.auth.models import User

from projector.tests.base import ProjectorTestCase
from projector.models import Project, Component

class ComponentTest(ProjectorTestCase):

    def setUp(self):
        self.client = Client()
        cred = 'componenter'
        self.user, created = User.objects.get_or_create(
            username = cred,
            email = 'componenter@example.com',
            is_superuser = True,
            is_active = True)
        self.user.set_password(cred)
        self.user.save()
        self.user._plain_password = cred
        self.project = Project.objects.create_project(
            name = 'component-test-project',
            slug = 'component-test-project',
            author = self.user,
        )

    def test_name_uniqueness(self):
        self.client.login(username = self.user.username,
            password = self.user._plain_password)

        new_component_name = u'component-1'
        self._get_response(
            url = self.project.get_component_add_url(),
            data = {'name': new_component_name},
            method = 'POST', follow = True)

        # By default one component is already defined so now there should be 2
        self.assertEqual(self.project.component_set.count(), 2)

        response = self._get_response(
            url = self.project.get_component_add_url(),
            data = {'name': new_component_name},
            method = 'POST', follow = True)

        # Should not be added as it has same name
        self.assertEqual(self.project.component_set.count(), 2)
        name_field_errors = response.context['form']._errors['name']
        self.assertTrue(len(name_field_errors) > 0,
            "Component with name '%s' for this project already exist "
            "so we shouldn't be able to add new one" % new_component_name)

        another_name = u'component-2'
        self._get_response(
            url = self.project.get_component_add_url(),
            data = {'name': another_name},
            method = 'POST', follow = True)
        self.assertEqual(self.project.component_set.count(), 3)

        # Should not allow to update name of the component to one already
        # existing
        component = Component.objects.get(project = self.project,
            name = another_name)
        response = self._get_response(
            url = component.get_edit_url(),
            data = {'name': new_component_name},
            method = 'POST', follow = True)
        name_field_errors = response.context['form']._errors['name']
        self.assertTrue(len(name_field_errors) > 0,
            "Component with name '%s' for this project already exist "
            "so we shouldn't be able to change old name '%s' to this one"
            % (new_component_name, component.name))




