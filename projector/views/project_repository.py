from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext as _
from django.http import HttpResponse

from projector.models import Project
from projector.settings import get_config_value
from projector.permissions import ProjectPermission
from projector.core.controllers import BaseView

from vcs.web.simplevcs.views import browse_repository, diff_file

class ProjectView(BaseView):

    perms = []
    GET_perms = []
    POST_perms = []

    def __init__(self, request, username, project_slug):
        self.request = request
        self.project = get_object_or_404(Project, slug=project_slug,
            author__username=username)
        self.author = self.project.author
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

    template_name = 'projector/project/repository/browse.html'
    perms = ProjectView.perms + ['read_repository_project']

    def __init__(self, request, username, project_slug, rel_repo_url='',
            revision='tip'):
        super(RepositoryBrowseView, self).__init__(request, username,
            project_slug)
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

class RepositoryFileDiffView(ProjectView):

    template_name = 'projector/project/repository/diff.html'

    def __init__(self, request, username, project_slug, revision_old,
            revision_new, rel_repo_url):
        super(RepositoryFileDiffView, self).__init__(request, username,
            project_slug)
        self.revision_old = revision_old
        self.revision_new = revision_new
        self.rel_repo_url = rel_repo_url

    def __call__(self):
        diff_info = {
            'repository': self.project.repository,
            'revision_old': self.revision_old,
            'revision_new': self.revision_new,
            'file_path': self.rel_repo_url,
            'template_name': self.template_name,
            'extra_context': {
                'project': self.project,
            },
        }
        return diff_file(self.request, **diff_info)

class RepositoryFileRaw(ProjectView):

    def __init__(self, request, username, project_slug, revision, rel_repo_url):
        super(RepositoryFileRaw, self).__init__(request, username, project_slug)
        self.revision = revision
        self.rel_repo_url = rel_repo_url

    def __call__(self):
        node = self.project.repository.request(self.rel_repo_url, self.revision)
        response = HttpResponse(node.content, mimetype=node.mimetype)
        response['Content-Disposition'] = 'attachment; filename=%s' % node.name
        return response

class RepositoryFileAnnotate(ProjectView):

    template_name='projector/project/repository/annotate.html'

    def __init__(self, request, username, project_slug, revision, rel_repo_url):
        super(RepositoryFileAnnotate, self).__init__(request, username,
            project_slug)
        self.revision = revision
        self.rel_repo_url = rel_repo_url

    def __call__(self):
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

class RepositoryChangesets(ProjectView):

    template_name = 'projector/project/repository/changeset_list.html'

    def __call__(self):
        context = {
            'project': self.project,
        }
        context['repository'] = self.project.repository
        context['CHANGESETS_PAGINATE_BY'] = get_config_value(
            'CHANGESETS_PAGINATE_BY')
        return render_to_response(self.template_name, context,
            RequestContext(self.request))

