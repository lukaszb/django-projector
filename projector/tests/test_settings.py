import inspect

from django.test import TestCase

from projector import settings
from projector.models import Project
from projector.forms import ProjectCreateForm
from projector.forms import ProjectMembershipPermissionsForm
from projector.forms import ProjectTeamPermissionsForm
from projector.forks import BaseExternalForkForm
from projector.utils.basic import str2obj
from projector.views.users import can_fork_external

from guardian.shortcuts import get_perms_for_model

class SettingsTest(TestCase):

    def setUp(self):
        """
        Remember settings at the beginning of the test.
        """
        members = inspect.getmembers(settings)
        self._settings = dict(((key, val) for key, val in members
            if key.isupper()))

    def tearDown(self):
        """
        Reset settings to default values.
        """
        for key, val in self._settings.items():
            setattr(settings, key, val)

    def test_PRIVATE_ONLY(self):
        settings.PRIVATE_ONLY = False
        form = ProjectCreateForm()
        self.assertEqual(len(form.fields['public'].choices), 2)

        settings.PRIVATE_ONLY = True
        form = ProjectCreateForm()
        self.assertEqual(len(form.fields['public'].choices), 1)
        self.assertEqual(form.fields['public'].choices[0][0], u'private')

    def test_EDITABLE_PERMISSIONS(self):
        all_perms = set([p.codename for p in get_perms_for_model(Project)])
        editable_perms = set(settings.get_config_value('EDITABLE_PERMISSIONS'))
        self.assertTrue(editable_perms.issubset(all_perms))
        self.assertTrue('add_project' not in editable_perms,
            "EDITABLE_PERMISSIONS cannot contain add_project permission as "
            "it is global, not object-specific")

        form = ProjectMembershipPermissionsForm()
        form_perms = set((c[0] for c in form.fields['permissions'].choices))
        self.assertTrue(form_perms == editable_perms)

        form = ProjectTeamPermissionsForm()
        form_perms = set((c[0] for c in form.fields['permissions'].choices))
        self.assertTrue(form_perms == editable_perms)

    def test_FORK_FORMS(self):
        map = settings.FORK_EXTERNAL_MAP.items()
        for key, val in map:
            ForkForm = str2obj(val)
            self.assertTrue(issubclass(ForkForm, BaseExternalForkForm))

    def test_FORK_EXTERNAL_both_on(self):
        settings.FORK_EXTERNAL_ENABLED = True
        settings.FORK_EXTERNAL_MAP = {'not': 'empty'}
        self.assertTrue(can_fork_external())

    def test_FORK_EXTERNAL_both_off(self):
        settings.FORK_EXTERNAL_ENABLED = False
        settings.FORK_EXTERNAL_MAP = {}
        self.assertFalse(can_fork_external())

    def test_FORK_EXTERNAL_mix(self):
        settings.FORK_EXTERNAL_MAP = True
        settings.FORK_EXTERNAL_MAP = {}
        self.assertFalse(can_fork_external())

        settings.FORK_EXTERNAL_ENABLED = False
        settings.FORK_EXTERNAL_MAP = {'not': 'empty'}
        self.assertFalse(can_fork_external())

