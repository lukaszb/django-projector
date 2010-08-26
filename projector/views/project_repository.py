from django.contrib import messages
from django.utils.translation import ugettext as _
from django.http import HttpResponse
from django.shortcuts import redirect

from projector.views.project import ProjectView
from projector.utils.lazy import LazyProperty

from vcs.web.simplevcs.views import browse_repository, diff_file

class RepositoryView(ProjectView):

    perms_private = ['view_project', 'can_read_repository']

    @LazyProperty
    def has_errors(self):
        """
        Default error handling for repository-related views. See also
        ``get_error_response``.
        """
        response = None
        if not self.project.repository_id:
            messages.info(self.request, _("Project has no repository"))
            response = redirect(self.project)
        if not self.project._get_repo_path():
            msg = _("There is something wrong with project's repository")
            messages.error(self.request, msg)
            response = redirect(self.project)
        if not self.project.repository.revisions:
            messages.info(self.request, _("Repository has no changesets yet"))
            response = redirect(self.project)
        return response

    def get_error_response(self):
        """
        Combined with ``has_errors`` could be used like this::

            def response(self, request):
                if self.has_errors:
                    return self.get_error_response()
                ...

        """
        if self.has_errors:
            return self.has_errors
        return

class RepositoryBrowseView(RepositoryView):

    template_name = 'projector/project/repository/browse.html'

    def response(self, request, username, project_slug, rel_repo_url='',
            revision='tip'):
        if self.has_errors:
            return self.get_error_response()
        repo_info = {
            'repository': self.project.repository,
            'revision': revision,
            'node_path': rel_repo_url,
            'template_name': self.template_name,
            'extra_context': {
                'project': self.project,
            },
        }
        return browse_repository(self.request, **repo_info)

class RepositoryFileDiffView(RepositoryView):

    template_name = 'projector/project/repository/diff.html'

    def response(self, request, username, project_slug, revision_old,
            revision_new, rel_repo_url):
        if self.has_errors:
            return self.get_error_response()
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
        return diff_file(self.request, **diff_info)

class RepositoryFileRaw(RepositoryView):
    """
    This view returns FileNode from repository as file attachment.
    """

    def response(self, request, username, project_slug, revision, rel_repo_url):
        if self.has_errors:
            return self.get_error_response()
        node = self.project.repository.request(rel_repo_url, revision)
        response = HttpResponse(node.content, mimetype=node.mimetype)
        response['Content-Disposition'] = 'attachment; filename=%s' % node.name
        return response

class RepositoryFileAnnotate(RepositoryView):

    template_name='projector/project/repository/annotate.html'

    def response(self, request, username, project_slug, revision, rel_repo_url):
        if self.has_errors:
            return self.get_error_response()
        repo_info = {
                'repository': self.project.repository,
                'revision': revision,
                'node_path': rel_repo_url,
                'template_name': self.template_name,
                'extra_context': {
                    'project': self.project,
                },
            }
        return browse_repository(self.request, **repo_info)

class RepositoryChangesets(RepositoryView):

    template_name = 'projector/project/repository/changeset_list.html'

    def response(self, request, username, project_slug):
        if self.has_errors:
            return self.get_error_response()
        context = {
            'project': self.project,
        }
        context['repository'] = self.project.repository
        context['CHANGESETS_PAGINATE_BY'] = \
            self.project.config.changesets_paginate_by
        return context

