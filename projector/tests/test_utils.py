from django.test import TestCase

from projector.utils.email import extract_emails


class ExtractEmailsTest(TestCase):

    def test_extract_single(self):

        def test_email(email, text):
            emails = extract_emails(text)
            self.assertEqual(len(emails), 1, '\n'.join(('',
                "Tested email: %s" % email,
                "Tested text: %s" % text,
                "We should get exactly one email address from the given text")))
            self.assertEqual(emails[0], email, '\n'.join(('',
                "Tested email: %s" % email,
                "Tested text: %s" % text,
                "We should get exactly one email address from the given text")))

        pairs = (
            ('jodoe@example.com', 'jodoe@example.com'),
            ('jodoe@example.com', '<jodoe@example.com>'),
            ('j.doe@example.com', 'j.doe@example.com'),
            ('j.doe@example.com', 'J. Doe j.doe@example.com'),
            ('j.doe@example.com', 'J. Doe <j.doe@example.com>'),
            ('j.doe@example.com', 'J.Doe<j.doe@example.com>'),
            ('j.doe@example.com', 'J.Doe\n<j.doe@example.com>'),
            ('j.doe@example.com', 'foobar\t<j.doe@example.com>'),
            ('j.doe@example.com', 'foobar <j.doe@example.com>'),
            ('j.doe@example.com', 'foobar j.doe@example.com\nbaz'),
            ('j.doe@example.com', 'JDoe j.doe@example.com'),
            ('j.doe@example.com', 'j.doe@example.com J. Doe'),
        )
        for email, text in pairs:
            test_email(email, text)

    def test_extract_multiple(self):

        text = ("my email is lukaszbalcerzak@gmail.com and his: "
                "j.doe@example.com")

        self.assertEqual(
            set(('lukaszbalcerzak@gmail.com', 'j.doe@example.com')),
            set((extract_emails(text)))
        )

