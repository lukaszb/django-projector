from django.contrib import messages
from django.utils.translation import ugettext as _
from django.http import HttpResponse
from django.shortcuts import redirect

from projector.views.project import ProjectView
from projector.utils.lazy import LazyProperty

from vcs.web.simplevcs.views import browse_repository, diff_file, diff_changeset


class RepositoryView(ProjectView):
    """
    Base repository view.

    **View attributes**

    * ``perms_private``: ``['view_project', 'can_read_repository']``

    """

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
        elif not self.project._get_repo_path() or \
                self.project.repository is None:
            msg = _("There is something wrong with project's repository")
            messages.error(self.request, msg)
            response = redirect(self.project)
        elif not self.project.repository.revisions:
            messages.info(self.request, _("Repository has no changesets yet"))
            return RepositoryQuickstart(self.request, *self.args, **self.kwargs)
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


class RepositoryBrowse(RepositoryView):
    """
    Repository browsing view.

    In fact, this is only a wrapper for
    ``vcs.web.simplevcs.views.browse_repository`` view.

    **View attributes**

    * ``template_name``: ``'projector/project/repository/browse.html'``

    **Wrapped view**

       .. autofunction:: vcs.web.simplevcs.views.browse_repository

    """

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


class RepositoryFileDiff(RepositoryView):
    """
    View presenting differences between two file nodes.

    In fact, this is only a wrapper for
    ``vcs.web.simplevcs.views.browse_repository`` view.

    **View attributes**

    * ``template_name``: ``'projector/project/repository/diff.html'``

    **Wrapped view**

       .. autofunction:: vcs.web.simplevcs.views.diff_file

    """

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
    This view returns ``FileNode`` from repository as file attachment.
    """

    def response(self, request, username, project_slug, revision, rel_repo_url):
        if self.has_errors:
            return self.get_error_response()
        changeset = self.project.repository.get_changeset(revision)
        node = changeset.get_node(rel_repo_url)
        response = HttpResponse(node.content, mimetype=node.mimetype)
        response['Content-Disposition'] = 'attachment; filename=%s' % node.name
        return response


class RepositoryFileAnnotate(RepositoryBrowse):
    """
    View presenting file from repository but with additional annotate
    information (shows changeset for which each line was added/changed).

    **View attributes**

    * ``template_name``: ``'projector/project/repository/annotate.html'``

    In fact, annotate is done at the template level.
    """

    template_name='projector/project/repository/annotate.html'


class RepositoryChangesetList(RepositoryView):
    """
    Shows list of changesets for requested project's repository.

    **View attributes**

    * ``template_name``: ``'projector/project/repository/changeset_list.html'``

    **Additional context variables**

    * ``repository``: repository for requested project
    * ``CHANGESETS_PAGINATE_BY``: number of changesets to be shown at
      template for each page. Taken from project configuration's
      ``changesets_paginate_by`` attribute.

    """

    template_name = 'projector/project/repository/changeset_list.html'

    def response(self, request, username, project_slug):
        if self.has_errors:
            return self.get_error_response()
        self.context['repository'] = self.project.repository
        self.context['CHANGESETS_PAGINATE_BY'] = \
            self.project.config.changesets_paginate_by
        return self.context


class RepositoryChangesetDetail(RepositoryView):
    """
    Shows detailed information about requested commit.

    In fact, this is only a wrapper for
    ``vcs.web.simplevcs.views.diff_changeset`` view.

    **View attributes**

    * ``template_name``: ``'projector/project/repository/changeset_detail.html'``

    **Wrapped view**

       .. autofunction:: vcs.web.simplevcs.views.diff_changeset

    """

    template_name = 'projector/project/repository/changeset_detail.html'

    def response(self, request, username, project_slug, revision):
        if self.has_errors:
            return self.get_error_response()
        diff_info = {
            'repository': self.project.repository,
            'revision': revision,
            'template_name': self.template_name,
            'extra_context': {
                'project': self.project,
            }
        }
        return diff_changeset(self.request, **diff_info)


class RepositoryQuickstart(RepositoryView):
    """
    Shows quickstart help for the project's repository.

    **View attributes**

    * ``template_name``: ``'projector/project/repository/quickstart.html'``.
    """

    template_name = 'projector/project/repository/quickstart.html'

    def response(self, request, username, project_slug):
        return self.context

