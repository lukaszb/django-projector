import logging

from django.test import TestCase
from django.contrib.auth.models import User, Group
#from django.core.urlresolvers import reverse
from django.test.client import Client

from projector.models import Project, Membership, Team

from guardian.shortcuts import assign

class ProjectorPermissionTests(TestCase):

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
        # Test public project for anonymous user
        self.client.logout()
        response = self.client.get(self.public_project.get_absolute_url())
        self.assertTrue(response.status_code == 200,
            "User %s doesn't have permission to view public project!"
            % user)

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

            self.private_project.get_task_list_url(),
            self.private_project.get_create_task_url(),
            self.private_project.get_milestones_url(),
            self.private_project.get_milestones_add_url(),
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
            email='new_member@example.com',
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
        self.client.logout()
        self.client.login(username=user.username, password=user._plain_password)
        url = self.private_project.get_absolute_url()
        resp = self.client.get(url)
        self.assertTrue(resp.status_code == 200,
            "User %s tried access GET %s but returned code was %s"
            % (user, url, resp.status_code))

        self.client.logout()

