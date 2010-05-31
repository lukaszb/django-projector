from itertools import chain

from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext as _

from projector.models import Project
from projector.settings import get_config_value
from projector.permissions import ProjectPermission

from vcs.web.simplevcs.views import browse_repository

from djclsview import View

class ProjectView(View):

    perms = ['view_project']
    GET_perms = []
    POST_perms = []
    template_name = 'projector/project/repository/browse.html'

    def __init__(self, request, username, project_slug, *args, **kwargs):
        self.project = get_object_or_404(Project, slug=project_slug,
            author__username=username)
        self.author = self.project.author
        args = list(chain(username, project_slug, *args))

        super(ProjectView, self).__init__(request, *args, **kwargs)
        self.check_permissions()

    def get_required_perms(self):
        if self.request.method == 'GET':
            return set(self.perms + self.GET_perms)
        elif self.request.method == 'POST':
            return set(self.perms + self.POST_perms)
        else:
            return self.perms

    def check_permissions(self):
        self.check = ProjectPermission(self.request.user)
        if (self.project.is_private() or not
            get_config_value('ALWAYS_ALLOW_READ_PUBLIC_PROJECTS')):
            for perm in self.get_required_perms():
                if not self.check.has_perm(perm, self.project):
                    raise PermissionDenied()

class RepositoryBrowseView(ProjectView):

    perms = ProjectView.perms + ['read_repository_project']

    def __init__(self, request, username, project_slug, rel_repo_url='',
            revision='tip', **kwargs):
        args = [request, username, project_slug] + \
            list([rel_repo_url, revision])
        super(RepositoryBrowseView, self).__init__(*args, **kwargs)
        self.rel_repo_url = rel_repo_url
        self.revision = revision

    def __call__(self):
        if not self.project._get_repo_path():
            msg = _("Repository's url is not set! Please configure project "
                    "preferences first.")
            messages.error(self.request, msg)
        repo_info = {
            'repository': self.project.repository,
            'revision': self.revision,
            'node_path': self.rel_repo_url,
            'template_name': self.template_name,
            'extra_context': {
                'project': self.project,
            },
        }
        return browse_repository(self.request, **repo_info)

