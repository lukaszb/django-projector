from django import forms
from django.utils.translation import ugettext as _

from projector.forks.base import BaseForkForm
from projector.models import Project

class BitbucketForkForm(BaseForkForm):

    site = 'bitbucket.org'
    help_text = _('Only public projects are allowed to be forked from '
                  'bitbucket')

    username = forms.CharField(max_length=128, label=_('Username'),
        help_text=_('Name of user you want to fork project from'))
    projectname = forms.CharField(max_length=128, label=_('Project name'),
        help_text=_('Name of project you want to fork belonging to specified '
                    'user'))
    use_https = forms.BooleanField(initial=False, label=_('Use https'),
        help_text=_('If checked, would clone project using secured '
                    'connection'), required=False)

    def fork(self, request):
        data = self.cleaned_data
        url = self.get_url()
        is_public = not bool(data['as_private'])
        project = Project.objects.create(
            author = request.user,
            name = data['projectname'],
            public = is_public,
            fork_url = url)
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

