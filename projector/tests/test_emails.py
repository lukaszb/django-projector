from django.core import mail
from django.test import TestCase

class EmailTest(TestCase):

    def test_send_email(self):
        subject = "Subject of the message"
        mail.send_mail(subject, "Message body", "from@localhost",
            ['to@example.com'], fail_silently=False)

        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].subject, subject)

