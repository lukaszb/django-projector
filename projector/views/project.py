import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator

from projector.decorators import permission_required_or_403

from projector.core.controllers import View
from projector.models import Project, Team
from projector.forms import ProjectForm
from projector.forms import TeamForm
from projector.forms import ProjectTeamPermissionsForm
from projector.permissions import ProjectPermission
from projector.settings import get_config_value

from vcs.web.simplevcs import settings as simplevcs_settings
from vcs.web.simplevcs.utils import get_mercurial_response, is_mercurial
from vcs.web.simplevcs.utils import log_error, basic_auth, ask_basic_auth
from vcs.web.simplevcs.exceptions import NotMercurialRequest

login_required_m = method_decorator(login_required)

class ProjectView(View):
    """
    Base class for all projector views.

    Logic should be implemented at ``__call__`` method. It does *NOT* accept
    any parameters.

    Would check necessary permissions defined by class attributes: ``perms``,
    ``GET_perms`` and ``POST_perms``. ``perms`` are always checked,
    ``GET_perms`` are additional checks which would be made for ``GET`` method
    requets only and ``POST_perms`` would be made for ``POST`` method requests.
    """

    perms = ['view_project']
    GET_perms = []
    POST_perms = []

    def __init__(self, request, username=None, project_slug=None, *args,
            **kwargs):
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
        if self.project.author == self.request.user:
            return
        self.check = ProjectPermission(self.request.user)
        if (self.project.is_private() or not
            get_config_value('ALWAYS_ALLOW_READ_PUBLIC_PROJECTS')):
            for perm in self.get_required_perms():
                fullperm = '.'.join((self.check.label, perm))
                if not self.check.has_perm(fullperm, self.project):
                    raise PermissionDenied()

class ProjectDetailView(ProjectView):
    """
    Returns selected project's detail for user given in ``request``.
    We make necessary permission checks *after* dispatching between
    normal and mercurial request, as mercurial requests has it's own
    permission requirements.
    """

    template_name = 'projector/project/details.html'
    csrf_exempt = True

    def get_required_perms(self):
        if is_mercurial(self.request):
            return []
        return super(ProjectDetailView, self).get_required_perms()

    def response(self, request, username, project_slug):
        try:
            if is_mercurial(request):
                return _project_detail_hg(request, self.project)
            last_part = request.path.split('/')[-1]
            if last_part and last_part != project_slug:
                raise Http404("Not a mercurial request and path longer than should "
                    "be: %s" % request.path)

            context = {
                'project': self.project,
            }
            return context
        except Exception, err:
            dont_log_exceptions = (PermissionDenied,)
            if not isinstance(err, dont_log_exceptions):
                log_error(err)
            raise err

def _project_detail_hg(request, project):
    """
    Wrapper for vcs.web.simplevcs.views.hgserve view as before we go any further
    we need to check permissions.
    TODO: Should use higher level simplevcs method
    """
    if not is_mercurial(request):
        msg = "_project_detail_hg called for non mercurial request"
        logging.error(msg)
        raise NotMercurialRequest(msg)

    if request.method not in ('GET', 'POST'):
        raise NotMercurialRequest("Only GET/POST methods are allowed, got %s"
            % request.method)
    # Allow to read from public projects
    if project.is_public() and request.method == 'GET' and \
        get_config_value('ALWAYS_ALLOW_READ_PUBLIC_PROJECTS'):
        mercurial_info = {
            'repo_path': project._get_repo_path(),
            'push_ssl': simplevcs_settings.PUSH_SSL,
        }
        return get_mercurial_response(request, **mercurial_info)

    # Check if user have been already authorized or ask to
    request.user = basic_auth(request)
    if request.user is None:
        return ask_basic_auth(request,
            realm=get_config_value('BASIC_AUTH_REALM'))

    check = ProjectPermission(request.user)

    if project.is_private() and request.method == 'GET' and\
        not check.read_repository_project(project):
        raise PermissionDenied("User %s cannot read repository for "
            "project %s" % (request.user, project))
    elif request.method == 'POST' and\
        not check.write_repository_project(project):
        raise PermissionDenied("User %s cannot write to repository "
            "for project %s" % (request.user, project))

    mercurial_info = {
        'repo_path': project._get_repo_path(),
        'push_ssl': simplevcs_settings.PUSH_SSL,
    }

    if request.user and request.user.is_active:
        mercurial_info['allow_push'] = request.user.username

    response = get_mercurial_response(request, **mercurial_info)
    return response

class ProjectListView(View):
    template_name = 'projector/project/list.html'

    def response(self, request):
        project_list = Project.objects.for_user(user=request.user)\
            .annotate(Count('task', distinct=True))
        context = {
            'project_list' : project_list,
        }
        return context

class ProjectCreateView(View):
    """
    New project creation view.
    """

    template_name = 'projector/project/create.html'

    @login_required_m
    def response(self, request, username=None):
        # TODO: what with username param? should it be required?
        # it's not used for now...
        project = Project(
            author=request.user,
        )
        form = ProjectForm(request.POST or None, instance=project)
        if request.method == 'POST' and form.is_valid():
            project = form.save()
            return HttpResponseRedirect(project.get_absolute_url())
        context = {
            'form' : form,
        }
        return context

class ProjectEditView(ProjectView):
    """
    Update project view.
    """

    template_name = 'projector/project/edit.html'
    perms = ProjectView.perms + ['change_project']

    def response(self, request, username, project_slug):
        project = self.project
        if project.public:
            project.public = u'public'
        else:
            project.public = u'private'
        form = ProjectForm(request.POST or None, instance=project)
        if request.method == 'POST' and form.is_valid():
            project = form.save()
            message = _("Project edited successfully")
            messages.success(request, message)
            return HttpResponseRedirect(project.get_absolute_url())

        context = {
            'form' : form,
            'project': form.instance,
        }
        return context

# ========================== #
# Membership - user & groups #
# ========================== #

# Teams

def project_teams(request, username, project_slug,
        template_name='projector/project/teams/home.html'):
    """
    Shows/updates project's teams view.
    """
    project = get_object_or_404(Project, slug=project_slug,
        author__username=username)
    if project.is_private():
        check = ProjectPermission(request.user)
        if not check.has_perm('project_permission.view_teams_project',
            project):
            raise PermissionDenied()
    teams = Team.objects.filter(project=project)

    context = {
        'project': project,
        'teams': teams,
    }
    return render_to_response(template_name, context, RequestContext(request))

@permission_required_or_403('project_permission.add_team_project',
    (Project, 'slug', 'project_slug', 'author__username', 'username'))
def project_teams_add(request, username, project_slug,
        template_name='projector/project/teams/add.html'):
    """
    Adds team for a project.
    """
    project = get_object_or_404(Project, slug=project_slug,
        author__username=username)
    team = Team(
        project = project,
    )
    form = TeamForm(request.POST or None, instance=team)

    if request.method == 'POST' and form.is_valid():
        logging.info("Saving team %s for project '%s'"
            % (form.instance.group, form.instance.project))
        form.save()
        return redirect(project.get_teams_url())
    elif form.errors:
        logging.error("Form contains errors:\n%s" % form.errors)

    context = {
        'project': form.instance.project,
        'form': form,
    }
    return render_to_response(template_name, context, RequestContext(request))

@permission_required_or_403('project_permission.change_team_project',
    (Project, 'slug', 'project_slug', 'author__username', 'username'))
def project_teams_edit(request, username, project_slug, name,
        template_name='projector/project/teams/edit.html'):
    """
    Manages settings and permissions of project's team.
    """
    team = get_object_or_404(Team, project__author__username=username,
        project__slug=project_slug, group__name=name)
    project = team.project
    team_permissions = team.perms
    codenames = [str(p.codename) for p in team_permissions]

    form = ProjectTeamPermissionsForm(request.POST or None,
        team = team,
        initial_permissions = codenames,
        request = request)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, _("Permissions updated"))
        else:
            messages.error(request,
                _("Errors occured while processing the form"))
        return redirect(team.get_absolute_url())
    context = {
        'project': project,
        'form': form,
        'team': team,
        'team_permissions': team_permissions,
    }

    return render_to_response(template_name, context, RequestContext(request))

