from django.core import mail
from django.contrib.auth.models import User
from django.test import TestCase

from projector.models import Project, Task

class EmailTest(TestCase):

    def test_send_email(self):
        subject = "Subject of the message"
        mail.send_mail(subject, "Message body", "from@localhost",
            ['to@example.com'], fail_silently=False)

        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].subject, subject)

    def test_send_mail_to_task_author(self):
        # needs project to be created first
        jack = User.objects.create(username='jack')
        project = Project.objects.create(author=jack, name='Black Jack')

