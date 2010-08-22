from django.contrib import messages
from django.utils.translation import ugettext as _
from django.http import HttpResponse, Http404

from projector.views.project import ProjectView

from vcs.exceptions import VCSError
from vcs.web.simplevcs.views import browse_repository, diff_file

class RepositoryView(ProjectView):

    perms_private = ['view_project', 'can_read_repository']

class RepositoryBrowseView(RepositoryView):

    template_name = 'projector/project/repository/browse.html'

    def response(self, request, username, project_slug, rel_repo_url='',
            revision='tip'):
        if not self.project._get_repo_path():
            msg = _("Repository's url is not set! Please configure project "
                    "preferences first.")
            messages.error(self.request, msg)
        repo_info = {
            'repository': self.project.repository,
            'revision': revision,
            'node_path': rel_repo_url,
            'template_name': self.template_name,
            'extra_context': {
                'project': self.project,
            },
        }
        try:
            return browse_repository(self.request, **repo_info)
        except VCSError:
            raise Http404

class RepositoryFileDiffView(RepositoryView):

    template_name = 'projector/project/repository/diff.html'

    def response(self, request, username, project_slug, revision_old,
            revision_new, rel_repo_url):
        diff_info = {
            'repository': self.project.repository,
            'revision_old': revision_old,
            'revision_new': revision_new,
            'file_path': rel_repo_url,
            'template_name': self.template_name,
            'extra_context': {
                'project': self.project,
            },
        }
        try:
            return diff_file(self.request, **diff_info)
        except VCSError:
            raise Http404

class RepositoryFileRaw(RepositoryView):
    """
    This view returns FileNode from repository as file attachment.
    """

    def response(self, request, username, project_slug, revision, rel_repo_url):
        node = self.project.repository.request(rel_repo_url, revision)
        response = HttpResponse(node.content, mimetype=node.mimetype)
        response['Content-Disposition'] = 'attachment; filename=%s' % node.name
        return response

class RepositoryFileAnnotate(RepositoryView):

    template_name='projector/project/repository/annotate.html'

    def response(self, request, username, project_slug, revision, rel_repo_url):
        repo_info = {
                'repository': self.project.repository,
                'revision': revision,
                'node_path': rel_repo_url,
                'template_name': self.template_name,
                'extra_context': {
                    'project': self.project,
                },
            }
        try:
            return browse_repository(self.request, **repo_info)
        except VCSError:
            raise Http404

class RepositoryChangesets(RepositoryView):

    template_name = 'projector/project/repository/changeset_list.html'

    def response(self, request, username, project_slug):
        context = {
            'project': self.project,
        }
        context['repository'] = self.project.repository
        context['CHANGESETS_PAGINATE_BY'] = \
            self.project.config.changesets_paginate_by
        return context

