from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.http import HttpResponse

from projector.views.project import ProjectView

from vcs.web.simplevcs.views import browse_repository, diff_file

class RepositoryView(ProjectView):
    private_perms = ProjectView.private_perms + ['can_read_repository']

class RepositoryBrowseView(RepositoryView):

    template_name = 'projector/project/repository/browse.html'

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

class RepositoryFileDiffView(RepositoryView):

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

class RepositoryFileRaw(RepositoryView):

    def __init__(self, request, username, project_slug, revision, rel_repo_url):
        super(RepositoryFileRaw, self).__init__(request, username, project_slug)
        self.revision = revision
        self.rel_repo_url = rel_repo_url

    def __call__(self):
        node = self.project.repository.request(self.rel_repo_url, self.revision)
        response = HttpResponse(node.content, mimetype=node.mimetype)
        response['Content-Disposition'] = 'attachment; filename=%s' % node.name
        return response

class RepositoryFileAnnotate(RepositoryView):

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

class RepositoryChangesets(RepositoryView):

    template_name = 'projector/project/repository/changeset_list.html'

    def __call__(self):
        context = {
            'project': self.project,
        }
        context['repository'] = self.project.repository
        context['CHANGESETS_PAGINATE_BY'] = \
            self.project.config.changesets_paginate_by
        return render_to_response(self.template_name, context,
            RequestContext(self.request))

