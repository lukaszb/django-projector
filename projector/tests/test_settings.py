from django.test import TestCase

from projector import settings
from projector.models import Project
from projector.forms import ProjectForm
from projector.forms import ProjectMembershipPermissionsForm
from projector.forms import ProjectTeamPermissionsForm

from guardian.shortcuts import get_perms_for_model

class SettingsTest(TestCase):

    def test_PRIVATE_ONLY(self):
        settings.PRIVATE_ONLY = False
        form = ProjectForm()
        self.assertEqual(len(form.fields['public'].choices), 2)

        settings.PRIVATE_ONLY = True
        form = ProjectForm()
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


