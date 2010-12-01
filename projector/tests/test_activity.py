import datetime

from django.test.client import Client
from django.contrib.auth.models import User

from projector.tests.base import ProjectorTestCase
from projector.models import Project


class ActivityTest(ProjectorTestCase):

    def setUp(self):
        self.client = Client()
        self.joe = User.objects.create_user('joe', 'joe@example.com', 'joe')
        self.jack = User.objects.create_user('jack', 'jack@example.com', 'jack')
        self.project = Project.objects.create(name='foobar', author=self.joe,
            public=True)
        self.private_project = Project.objects.create(name='private_foobar',
            author=self.joe, public=False)

    def test_project_created(self):
        actions = self.project.get_actions().all()
        self.assertEqual(actions.count(), 1)
        self.assertEqual(actions[0].verb, 'created')
        self.assertEqual(actions[0].is_public, self.project.public)

    def test_project_forked(self):
        fork = self.project.fork(self.jack)

        actions = fork.get_actions().all()
        self.assertEqual(actions.count(), 0)

        actions = self.project.get_actions().all()
        self.assertEqual(actions.count(), 2)
        self.assertEqual(actions[0].verb, 'forked')
        self.assertEqual(actions[1].verb, 'created')

    def test_project_action_with_custom_params(self):
        verb = "custom action taken"
        author = self.jack # other than author
        action_object = self.jack # other than project itself
        description = "Matrix has you" # any description
        public = not self.project.is_public() # other than project's public
        created_at = datetime.datetime(2010, 1, 1, 0, 0, 0) # custom date
        self.project.create_action(verb,
            author = author,
            action_object = action_object,
            description = description,
            is_public = public,
            created_at = created_at,
        )
        action = self.project.get_actions().get(created_at=created_at)
        self.assertEqual(action.verb, verb)
        self.assertEqual(action.description, description)
        self.assertEqual(action.action_object, action_object)
        self.assertEqual(action.project, self.project)

