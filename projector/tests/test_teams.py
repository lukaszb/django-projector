from django.test import TestCase
from django.contrib.auth.models import User, Group

from projector.forms import DashboardAddMemberForm

class DashboardAddMemberFormTest(TestCase):

    def setUp(self):
        self.group = Group.objects.create(name='admins')
        self.user = User.objects.create(username='admin')
        self.user.groups.add(self.group)
        profile = self.user.get_profile()
        profile.group = self.group
        profile.is_team = True
        profile.save()

    def test_wrong_user(self):
        data = {'user': 'not-existing-user-name'}
        form = DashboardAddMemberForm(self.group, data)
        self.assertFalse(form.is_valid())
        self.assertTrue('user' in form._errors)

    def test_wrong_username(self):
        wrong_usernames = (' ', '.', '*', 'joe!', '###', ',.<>')
        for username in wrong_usernames:
            data = {'user': username}
            form = DashboardAddMemberForm(self.group, data)
            self.assertFalse(form.is_valid())
            self.assertTrue('user' in form._errors)

    def test_proper_user(self):
        joe = User.objects.create(username='joe')
        data = {'user': joe.username}
        form = DashboardAddMemberForm(self.group, data)
        self.assertTrue(form.is_valid())

    def test_already_in_group(self):
        data = {'user': self.user.username}
        form = DashboardAddMemberForm(self.group, data)
        self.assertFalse(form.is_valid())
        self.assertTrue('user' in form._errors)

