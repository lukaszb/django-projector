from django import forms
from django.utils.translation import ugettext as _

from projector.core.exceptions import ForkError
from projector.forks.base import BaseExternalForkForm
from projector.models import Project

from vcs.exceptions import VCSError

class BitbucketForkForm(BaseExternalForkForm):

    site = 'bitbucket.org'
    help_text = _('Only public projects are allowed to be forked from '
                  'bitbucket')

    username = forms.RegexField(regex=r'^[-\w]+$', max_length=128,
        label=_('Username'),
        help_text=_('Name of user you want to fork project from'))
    projectname = forms.RegexField(regex=r'^[-\w]+$',max_length=128,
        label=_('Project name'),
        help_text=_('Name of project you want to fork belonging to specified '
                    'user'))
    use_https = forms.BooleanField(initial=False, label=_('Use https'),
        help_text=_('If checked, would clone project using secured '
                    'connection'), required=False)

    def clean_projectname(self):
        data = self.cleaned_data['projectname']
        if getattr(self, 'request', None) is not None:
            try:
                Project.objects.get(name=data, author=self.request.user)
                raise forms.ValidationError(_("Project with same name already "
                                              "exists"))
            except Project.DoesNotExist:
                pass
        return data

    def fork(self):
        """
        This method only creates ``Project`` instance with proper attributes
        as real fork is done by ``Project``'s ``post_save`` handler.
        """
        data = self.cleaned_data
        url = self.get_url()
        try:
            project = Project.objects.create_project(
                vcs_alias = 'hg',
                author = self.request.user,
                name = data['projectname'],
                public = self.is_public(),
                fork_url = url)
        except VCSError:
            raise ForkError(_("Error during fork procedure"))
        return project

    def get_url(self):
        if self.cleaned_data.get('use_https', False):
            schema = 'https'
        else:
            schema = 'http'
        url = '://'.join((schema, self.site))
        username = self.cleaned_data['username']
        projectname = self.cleaned_data['projectname']
        url = '/'.join((url, username, projectname))
        return url

