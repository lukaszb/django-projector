from django.core import mail
from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse

from projector.models import Task, Team, Membership

class EmailTest(TestCase):

    fixtures = ['test_data.json']

    def setUp(self):
        self.client = Client()

    def _create_task(self, user, project, summary='Task summary',
        description='Example description', watch_changes=True):
        """
        Creates task for given parameters. Assumes given user is already
        logged in by ``self.client``.

        Returns created task.
        """
        task = Task.objects.get_for_project(project)
        data = {
            'summary': summary,
            'description': description,
            'status': task.status_id,
            'priority': task.priority_id,
            'type': task.type_id,
            'owner': user.username,
            'component': task.component_id,
        }
        if watch_changes:
            data['watch_changes'] = u'on'
        response = self.client.post(reverse('projector_task_create', kwargs={
            'username': user.username,
            'project_slug': project.slug}),
            data=data,
            follow=True)
        self.assertEqual(response.status_code, 200)
        return user.task_set.filter(project=project).order_by('-created_at')[0]

    def test_tasks_notification(self):
        # needs project to be created first
        jack = User.objects.get(username='jack')

        self.client.login(username='jack', password='jack')
        project = jack.project_set.all()[0]

        task = self._create_task(user=jack, project=project)

        # Author of the project should be notified after task is created
        self.assertEquals(len(mail.outbox), 1)

        joe = User.objects.get(username='joe')
        self.client.login(username='joe', password='joe')
        task.watch(joe)

        # After joe started to watch task, calling ``notify`` should send one
        # mail with both jack and joe in recipient list
        task.notify()
        self.assertEquals(len(mail.outbox), 2)
        self.assertEquals(
            set([jack.email, joe.email]),
            set(mail.outbox[1].recipients())
        )

        # If we set recipient list arbitrary we expect only those recipients
        # would receive the message
        recipient_list = [joe.email]
        task.notify(recipient_list=recipient_list)
        self.assertEquals(len(mail.outbox), 3)
        self.assertEquals(recipient_list, mail.outbox[2].recipients())

        # If project is private we need to ensure only members and author/owner
        # would receive the message
        task.project.public = False
        task.project.save()
        task.notify()
        self.assertEquals(len(mail.outbox), 4)
        self.assertEquals([jack.email], mail.outbox[3].recipients())

        # But if joe would join Team associated with task's project then he
        # could get the message
        group = Group.objects.create(name='jack-n-joe')
        joe.groups.add(group)
        Team.objects.create(group=group, project=task.project)
        task.notify()
        self.assertEquals(len(mail.outbox), 5)
        self.assertEquals(
            set([jack.email, joe.email]),
            set(mail.outbox[4].recipients()),
        )

        # Membership would be enough, too
        joe.groups.remove(group)
        Membership.objects.create(project=task.project, member=joe)
        task.notify()
        self.assertEquals(len(mail.outbox), 6)
        self.assertEquals(
            set([jack.email, joe.email]),
            set(mail.outbox[5].recipients()),
        )

