from django.contrib.auth.models import User, Group, AnonymousUser
from django.core.exceptions import ValidationError

from projector.tests.base import ProjectorTestCase
from projector.models import Team, Project


class UserToTeamConversion(ProjectorTestCase):

    def setUp(self):
        self.jack = User.objects.create_user(
            username = 'jack',
            email = 'jack@example.com',
            password = 'jack')

    def test_conversion(self):
        profile = self.jack.get_profile()
        self.assertFalse(profile.is_team)
        self.assertEqual(profile.group, None)

        project1 = Project.objects.create(name='project1', author=self.jack)
        project2 = Project.objects.create(name='project2', author=self.jack)
        group = Team.objects.convert_from_user(self.jack)

        self.assertTrue(profile.is_team)
        self.assertEqual(profile.group, group)
        self.assertTrue(group in self.jack.groups.all())

        self.assertTrue(group in Group.objects.filter(team__project=project1))
        self.assertTrue(group in Group.objects.filter(team__project=project2))

    def test_integrity(self):
        Group.objects.create(name='jack')
        try:
            Team.objects.convert_from_user(self.jack)
        except ValidationError:
            pass
        else:
            self.fail("Cannot allow to convert user into team if there is "
                      "a group with same name already persisted")

    def test_anonymous(self):
        user = AnonymousUser()
        try:
            Team.objects.convert_from_user(user)
        except ValidationError:
            pass
        else:
            self.fail("Cannot allow to convert anonymous user to team")

    def test_staff(self):
        self.jack.is_staff = True
        self.jack.save()
        try:
            Team.objects.convert_from_user(self.jack)
        except ValidationError:
            pass
        else:
            self.fail("Cannot allow to convert staff member to team")

    def test_superuser(self):
        self.jack.is_superuser = True
        self.jack.save()
        try:
            Team.objects.convert_from_user(self.jack)
        except ValidationError:
            pass
        else:
            self.fail("Cannot allow to convert superuser to team")

    def test_non_active(self):
        self.jack.is_active = False
        self.jack.save()
        try:
            Team.objects.convert_from_user(self.jack)
        except ValidationError:
            pass
        else:
            self.fail("Cannot allow to convert inactive user to team")


