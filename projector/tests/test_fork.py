from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User, AnonymousUser
from django.core.exceptions import PermissionDenied

from projector.core.exceptions import ForkError
from projector.models import Project
from projector.tests.base import ProjectorTestCase

class ForkTest(TestCase):

    def setUp(self):
        self.anon = AnonymousUser()
        self.joe = User.objects.create(username='joe')
        self.project = Project.objects.create(name='project', author=self.joe)


    def test_anonymous(self):
        """
        AnonymousUser cannot fork projects.
        """

        self.assertRaises(PermissionDenied, self.project.fork, user=self.anon)

    def test_inactive(self):
        """
        Inactive users cannot fork projects.
        """
        jack = User.objects.create(username='jack', is_active=False)
        self.assertRaises(PermissionDenied, self.project.fork, user=jack)

    def test_not_viewable(self):
        """
        If user cannot view project he/she cannot fork it either.
        """
        Project.objects.filter(id=self.project.id).update(public=False)
        jack = User.objects.create(username='jack')
        self.assertRaises(PermissionDenied, self.project.fork, user=jack)

    def test_same_author(self):
        """
        User cannot fork his/her own project.
        """
        self.assertRaises(ForkError, self.project.fork, user=self.project.author)

    def test_already_forked(self):
        """
        User cannot fork same project twice. Tests ``get_fork_for_user`` method
        too.
        """
        jack = User.objects.create(username='jack')
        jack_fork = self.project.fork(user=jack)
        f = self.project.get_fork_for_user(jack)
        self.assertTrue(jack_fork.id == f.id,
            "fork method returned %s (id=%s) and get_fork_for_user returned "
            "%s (id=%s)" % (jack_fork, jack_fork.id, f, f.id))

        jacky = User.objects.create(username='jacky')
        jacky_fork = self.project.fork(user=jacky)
        f = self.project.get_fork_for_user(jacky)
        self.assertTrue(jacky_fork.id == f.id,
            "fork method returned %s (id=%s) and get_fork_for_user returned "
            "%s (id=%s)" % (jacky_fork, jacky_fork.id, f, f.id))

        jade = User.objects.create(username='jade')
        jade_fork = jack_fork.fork(user=jade)
        f = self.project.get_fork_for_user(jade)
        self.assertTrue(jade_fork.id == f.id,
            "fork method returned %s (id=%s) and get_fork_for_user returned "
            "%s (id=%s)" % (jack_fork, jack_fork.id, f, f.id))
        jacky_fork.name = 'changed-name'
        self.assertRaises(ForkError, jacky_fork.fork, user=jade)

    def test_force_private(self):
        jack = User.objects.create(username='jack')
        fork = self.project.fork(user=jack, force_private=True)
        self.assertFalse(fork.public)


class ForkViewTest(ProjectorTestCase):

    def setUp(self):
        self.joe = User.objects.create_user(username='joe',
            email='joe@example.com', password='joe')
        self.project = Project.objects.create(name='project', author=self.joe)
        self.jack = User.objects.create_user(username='jack',
            email='jack@example.com', password='jack')
        self.client = Client()

    def test_fork(self):
        self.assertFalse(self.project.is_fork())
        self.client.login(username='jack', password='jack')

        # Jack goes to joe's project page
        url = self.project.get_absolute_url()
        response = self._get_response(url)
        self.assertEqual(response.context['user_fork'], None)
        self.assertEqual(response.context['forks'],
            [response.context['project']])

        # Jack forks joe's project
        url = self.project.get_fork_url()
        response = self._get_response(url, {
            'submit': u'Fork project'},
            method='POST', follow=True)
        fork = response.context['project']
        self.assertTrue(fork.is_fork())
        self.assertEqual(fork.get_root().id, self.project.id)

        self.assertEqual(fork.repository.alias, self.project.repository.alias)
        self.assertEqual(fork.repository.revisions,
            self.project.repository.revisions)

