from django.test import TestCase

from projector.utils.helpers import Choices

class ChoicesTest(TestCase):

    def test(self):

        class Status(Choices):
            FIRST = 1
            SECOND = 2
            THIRD = 3

        choices = Status.as_choices()

        self.assertEqual(choices,
            [
                (1, u'First'),
                (2, u'Second'),
                (3, u'Third'),
            ]
        )

    def test_with_underscore(self):

        class Status(Choices):
            FIRST = 1
            SECOND = 2
            THIRD_AND_LAST = 3

        choices = Status.as_choices()

        self.assertEqual(choices,
            [
                (1, u'First'),
                (2, u'Second'),
                (3, u'Third and last'),
            ]
        )

    def test_with_not_all_uppered(self):

        class Status(Choices):
            FIRST = 1
            SECOND = 2
            third = 3

        choices = Status.as_choices()

        self.assertEqual(choices,
            [
                (1, u'First'),
                (2, u'Second'),
            ]
        )

    def test_with_no_integers(self):

        class Status(Choices):
            FIRST = 1
            SECOND = 2
            THIRD = 'third'

        choices = Status.as_choices()

        self.assertEqual(choices,
            [
                (1, u'First'),
                (2, u'Second'),
            ]
        )

    def test_order(self):

        class Status(Choices):
            SECOND = 2
            NEXT = 900
            THIRD = 3
            ERROR = -1
            FIRST = 1

        choices = Status.as_choices()
        ints = [c[0] for c in choices]
        self.assertEqual(ints, [-1, 1, 2, 3, 900])

