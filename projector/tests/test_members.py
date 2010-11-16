from django.contrib.auth.models import User
from django.test.client import Client

from projector.forms import MembershipForm
from projector.models import Project
from projector.tests.base import ProjectorTestCase

from urlparse import urlsplit


class MembershipTest(ProjectorTestCase):

    def setUp(self):
        self.user = User.objects.create_user('joe', 'joe@example.com', 'joe')
        # Emulate project setup
        self.project = Project.objects.create(name='foobar', author=self.user,
            state=100)
        self.project.set_memberships()
        self.project.set_author_permissions()
        self.project.create_config()
        self.client = Client()
        self.client.login(username='joe', password='joe')

    def _check_members(self, project, members):
        """
        Checks if current memberships related to given ``project`` are same
        as given ``members`` (list of users).
        """
        members_url = self.project.get_members_url()
        response = self._get_response(members_url)
        members = set(members)
        current_members = set([m.member for m in
            response.context['memberships']])
        self.assertEqual(members, current_members)

    def test_add_member(self):
        """
        Tests new member creation view. Returns added member.
        """
        jack = User.objects.create_user('jack', 'jack@example.com', 'jack')
        url = self.project.get_members_add_url()
        response = self._get_response(url)
        self.assertTrue(isinstance(response.context['form'], MembershipForm))
        response = self._get_response(url, data={'member': jack.username},
            method='POST', follow=True)
        self._check_members(self.project, [self.user, jack])
        return jack

    def test_cannot_add_same_member(self):
        member = self.test_add_member()
        url = self.project.get_members_add_url()
        response = self._get_response(url, data={'member': member.username},
            method='POST', follow=True)
        self.assertEqual(len(response.redirect_chain), 0)
        self.assertTrue(response.context['form'])
        self.assertTrue(response.context['form'].errors)
        self.assertTrue('member' in response.context['form'].errors)

    def test_delete_member(self):
        member = self.test_add_member()
        url = self.project.get_members_delete_url(member.username)
        response = self._get_response(url)
        response = self._get_response(url, data={'post': True},
            method='POST', follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self._check_members(self.project, [self.user])

    def test_cannod_delete_not_member(self):
        url = self.project.get_members_delete_url('nouser')
        # Test codes only
        self._get_response(url, code=404)
        self._get_response(url, data={'post': True}, method='POST', code=404)

    def test_cannot_delete_author(self):
        url = self.project.get_members_delete_url(self.user.username)
        response = self._get_response(url, follow=True)
        response = self._get_response(url, data={'post': True},
            method='POST', follow=True)
        members_url = self.project.get_members_url()
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(urlsplit(response.redirect_chain[0][0]).path,
            members_url)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.status_code, 200)

        self._check_members(self.project, [self.user])

