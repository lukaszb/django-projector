from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User, AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest

from projector.core.exceptions import ProjectorError, ForkError
from projector.models import Project
from projector.tests.base import ProjectorTestCase
from projector.forks.base import BaseExternalForkForm
from projector.forks.bitbucket import BitbucketForkForm
from projector.forks.github import GithubForkForm

class ForkTest(TestCase):

    def setUp(self):
        self.anon = AnonymousUser()
        self.joe = User.objects.create(username='joe')
        self.project = Project.objects.create_project(name='project',
            author=self.joe)


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
        self.project = Project.objects.create_project(name='project',
            author=self.joe)
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

        if self.project.repository is not None:
            self.assertEqual(fork.repository.alias,
                self.project.repository.alias,
                "Alias of fork (%s) should be same as alias of original "
                "project (%s)" % (fork, self.project))
            self.assertEqual(fork.repository.revisions,
                self.project.repository.revisions)


class BaseExternalForkFormTest(TestCase):

    def setUp(self):
        self.request = HttpRequest()

    def test_not_cleaned_no_data(self):
        form = BaseExternalForkForm()
        form.request = self.request
        self.assertRaises(ProjectorError, form.is_public)
        self.assertRaises(ProjectorError, form.is_private)

    def test_not_cleaned_with_data(self):
        form = BaseExternalForkForm({'as_private': u'checked'})
        form.request = self.request
        self.assertRaises(ProjectorError, form.is_public)
        self.assertRaises(ProjectorError, form.is_private)

    def test_valid_public(self):
        form = BaseExternalForkForm({})
        form.request = self.request
        self.assertTrue(form.is_valid())
        # as_private not checked
        self.assertTrue(form.is_public())
        self.assertFalse(form.is_private())

    def test_valid_private(self):
        form = BaseExternalForkForm({'as_private': u'checked'})
        form.request = self.request
        self.assertTrue(form.is_valid())
        # as_public checked
        self.assertFalse(form.is_public())
        self.assertTrue(form.is_private())


class BitbucketForkTest(TestCase):

    def setUp(self):
        self.request = HttpRequest()
        self.request.user = User.objects.create(username='joe')

    def test_fork(self):
        data = {
            'username': u'marcinkuzminski',
            'projectname': u'vcs',
            'as_private': u'checked',
        }
        form = BitbucketForkForm(data)
        form.request = self.request
        self.assertTrue(form.is_valid())
        fork = form.fork()
        fork = Project.objects.get(pk=fork.pk)
        self.assertTrue(len(fork.repository.revisions) > 100)
        changeset = fork.repository.get_changeset()
        self.assertTrue(changeset.get_node('setup.py') is not None)
        self.assertTrue(fork.is_private())

    def test_fork_with_same_name(self):
        Project.objects.create(name=u'joe-project', author=self.request.user)
        data = {
            'username': u'whatever',
            'projectname': u'joe-project',
            'as_private': u'checked',
        }
        form = BitbucketForkForm(data)
        form.request = self.request
        self.assertFalse(form.is_valid())

    def test_valid(self):
        """
        This test checks if sane values have been passed to the form.
        Allowing external forking may be very dangerous as we may expose
        own project to be used as *proxy* for attacks on external locations.
        """
        data_list = [dict((key, val) for key, val in (
            ('foobar', '<script...'),
            ('<script', 'foobar'),
            ('foobar', '../../'),
            ('../../', 'foobar'),
        ))]
        for data in data_list:
            form = BitbucketForkForm(data)
            form.request = self.request
            self.assertFalse(form.is_valid())


class GithubForkTest(TestCase):

    def setUp(self):
        self.request = HttpRequest()
        self.request.user = User.objects.create(username='mirror')

    def test_fork(self):
        data = {
            'username': u'lukaszb',
            'projectname': u'django-guardian',
            #'as_private': u'checked',
        }
        form = GithubForkForm(data)
        form.request = self.request
        self.assertTrue(form.is_valid())
        fork = form.fork()
        fork = Project.objects.get(pk=fork.pk)
        self.assertTrue(len(fork.repository.revisions) > 5)
        changeset = fork.repository.get_changeset()
        self.assertTrue(changeset.get_node('setup.py') is not None)
        self.assertFalse(fork.is_private())

    def test_fork_with_same_name(self):
        Project.objects.create(name=u'mirror-same', author=self.request.user)
        data = {
            'username': u'whatever',
            'projectname': u'mirror-same',
            'as_private': u'checked',
        }
        form = GithubForkForm(data)
        form.request = self.request
        self.assertFalse(form.is_valid())

    def test_valid(self):
        """
        This test checks if sane values have been passed to the form.
        Allowing external forking may be very dangerous as we may expose
        own project to be used as *proxy* for attacks on external locations.
        """
        data_list = [dict((key, val) for key, val in (
            ('foobar', '<script...'),
            ('<script', 'foobar'),
            ('foobar', '../../'),
            ('../../', 'foobar'),
        ))]
        for data in data_list:
            form = GithubForkForm(data)
            form.request = self.request
            self.assertFalse(form.is_valid())

