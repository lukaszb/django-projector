import urlparse

from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.test.client import Client

from projector.tests.base import ProjectorTestCase
from projector.models import Project, Membership, Team

from guardian.shortcuts import assign

class ProjectorPermissionTests(ProjectorTestCase):

    fixtures = ['test_data.json']

    def setUp(self):
        self.client = Client()

        self.admin = User.objects.get(username='admin')
        self.admin._plain_password = 'admin'

        self.jack = User.objects.get(username='jack')
        self.jack._plain_password = 'jack'

        self.joe = User.objects.get(username='joe')
        self.joe._plain_password = 'joe'

        self.noperms = User.objects.get(username='noperms')
        self.noperms._plain_password = 'noperms'

        # Create projects
        self.public_project = Project.objects.get(name='public project')
        self.private_project = Project.objects.get(name='private project')

    def test_anonymous(self):
        # Test public project for anonymous user
        self.client.logout()

        url = self.public_project.get_absolute_url()
        self._get_response(url)

        url = reverse('projector_project_create')
        response = self._get_response(url, follow=True)
        # Redirects directly to login page with next parameter
        self.assertTrue(len(response.redirect_chain) == 1)
        passed_url, passed_code = response.redirect_chain[0]
        parsed = urlparse.urlparse(passed_url)
        self.assertEqual(parsed.path, reverse('auth_login'))
        self.assertEqual(parsed.query, 'next=%s' % url)

    def test(self):

        # =================== #
        # Test public project #
        # =================== #

        for user in (self.admin, self.noperms, self.joe, self.jack):
            client = self.client
            client.login(username=user.username, password=user._plain_password)
            url = self.public_project.get_absolute_url()
            response = client.get(url)
            self.assertTrue(response.status_code == 200,
                "User %s doesn't have permission to view public project!"
                % user)
            client.logout()

        # ==================== #
        # Test private project #
        # ==================== #

        user = self.jack
        client = self.client
        client.login(username=user.username, password=user._plain_password)

        urls = (
            self.private_project.get_absolute_url(),
            self.private_project.get_edit_url(),
            self.private_project.get_members_url(),
            self.private_project.get_members_add_url(),
            #self.private_project.get_members_edit_url(),
            self.private_project.get_teams_url(),
            self.private_project.get_teams_add_url(),
            #self.private_project.get_teams_edit_url(),
            self.private_project.get_fork_url(),
            self.private_project.get_state_url(),

            self.private_project.get_task_list_url(),
            self.private_project.get_create_task_url(),
            self.private_project.get_milestones_url(),
            self.private_project.get_milestone_add_url(),
            self.private_project.get_components_url(),
            self.private_project.get_component_add_url(),
            self.private_project.get_workflow_url(),
            self.private_project.get_workflow_edit_url(),
            self.private_project.get_workflow_add_status_url(),
            self.private_project.get_browse_repo_url(),
            self.private_project.get_changesets_url(),
        )
        for url in urls:
            response = self.client.get(url)
            self.assertTrue(response.status_code == 403,
                "User %s tried to access %s but returned code was %s"
                % (user, url, response.status_code))

        # Now we add member and a team to the project and check if
        # they cannot be edited
        new_member = User.objects.create_user(
            username='new_member',
            email='new_member@non-existence-1231231.com',
            password='new_member')
        new_member._plain_password = 'new_member'

        Membership.objects.create(member=new_member,
            project=self.private_project)

        new_group = Group.objects.create(name='new_team')
        team = Team.objects.create(group=new_group,
            project=self.private_project)

        responses = (
            self.client.get(
                self.private_project.get_members_edit_url(new_member.username)),
            self.client.post(
                self.private_project.get_members_edit_url(new_member.username),
                data = {}),
            self.client.get(
                self.private_project.get_teams_edit_url(team.group.name)),
            self.client.post(
                self.private_project.get_teams_edit_url(team.group.name),
                data = {}),
        )
        for response in responses:
            self.assertTrue(response.status_code == 403,
                "User %s tried to access %s %s but returned code was %s"
                % (user, response.request['REQUEST_METHOD'],
                    response.request['PATH_INFO'], response.status_code))

        # Test project listing
        url = reverse('projector_project_list')
        resp = self._get_response(url)

        project_list = resp.context['project_list']
        for_user = Project.objects.for_user(user)
        self.assertEqual(set(project_list), set(for_user),
            "Project list retrieved from page (%s) is not equal with list for "
            "user (%s)" % (project_list, for_user))

        # Now we make jack a member but without permissions he shouldn't be
        # able to see anything new
        Membership.objects.create(member=user, project=self.private_project)
        for url in urls:
            response = self.client.get(url)
            self.assertTrue(response.status_code == 403,
                "User %s tried to access %s but returned code was %s"
                % (user, url, response.status_code))

        responses = (
            self.client.get(
                self.private_project.get_members_edit_url(new_member.username)),
            self.client.post(
                self.private_project.get_members_edit_url(new_member.username),
                data = {}),
            self.client.get(
                self.private_project.get_teams_edit_url(team.group.name)),
            self.client.post(
                self.private_project.get_teams_edit_url(team.group.name),
                data = {}),
        )
        for response in responses:
            self.assertTrue(response.status_code == 403,
                "User %s tried to access %s %s but returned code was %s"
                % (user, response.request['REQUEST_METHOD'],
                    response.request['PATH_INFO'], response.status_code))

        # We add "view_project" permission for jack
        assign('view_project', user, self.private_project)
        url = self.private_project.get_absolute_url()
        self._get_response(url)

        urls = (
            self.private_project.get_components_url(),
            self.private_project.get_milestones_url(),
            self.private_project.get_workflow_url(),
            self.private_project.get_state_url(),
        )
        for ulr in urls:
            self._get_response(url, code=200)

        self.client.logout()

