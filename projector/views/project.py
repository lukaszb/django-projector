import logging
import pprint

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.utils.translation import ugettext as _

from annoying.decorators import render_to

from authority.decorators import permission_required_or_403
from authority.models import Permission

from projector.models import Project, Membership, Team, Task
from projector.models import Milestone, Status, Transition, Component
from projector.forms import ProjectForm, MembershipForm, MilestoneForm
from projector.forms import StatusForm, StatusFormSet, ComponentForm
from projector.forms import TeamForm
from projector.permissions import ProjectPermission, get_or_create_permisson
from projector.filters import TaskFilter
from projector import settings as projector_settings

from richtemplates.shortcuts import get_first_or_None

from vcs.web.simplevcs import settings as simplevcs_settings
from vcs.web.simplevcs.utils import get_mercurial_response, is_mercurial
from vcs.web.simplevcs.utils import log_error, basic_auth, ask_basic_auth
from vcs.web.simplevcs.exceptions import NotMercurialRequest
from vcs.web.simplevcs.views import browse_repository

def project_details(request, project_slug,
        template_name='projector/project/details.html'):
    """
    Returns selected project's detail for user given in ``request``.
    We make necessary permission checks *after* dispatching between
    normal and mercurial request, as mercurial requests has it's own
    permission requirements.
    """
    try:
        project = get_object_or_404(Project, slug=project_slug)
        if is_mercurial(request):
            return _project_detail_hg(request, project)
        last_part = request.path.split('/')[-1]
        if last_part and last_part != project_slug:
            raise Http404("Not a mercurial request and path longer than should "
                "be: %s" % request.path)
        if project.is_private():
            check = ProjectPermission(user=request.user)
            if not check.view_project(project):
                raise PermissionDenied()
        context = {
            'project': project,
        }
        return render_to_response(template_name, context,
            RequestContext(request))
    except Exception, err:
        dont_log_exceptions = (PermissionDenied,)
        if not isinstance(err, dont_log_exceptions):
            log_error(err)
        raise err

project_details.csrf_exempt = True

def _project_detail_hg(request, project):
    """
    Wrapper for vcs.web.simplevcs.views.hgserve view as before we go any further
    we need to check permissions.
    TODO: Should use higher level simplevcs method
    """
    #realm = projector_settings.BASIC_AUTH_REALM
    if not is_mercurial(request):
        msg = "_project_detail_hg called for non mercurial request"
        logging.error(msg)
        raise NotMercurialRequest(msg)

    if request.method not in ('GET', 'POST'):
        raise NotMercurialRequest("Only GET/POST methods are allowed, got %s"
            % request.method)
    # Allow to read from public projects
    if project.is_public() and request.method == 'GET' and \
        projector_settings.ALWAYS_ALLOW_READ_PUBLIC_PROJECTS:
        return get_mercurial_response(request,
            repo_path=project._get_repo_path())

    # Check if user have been already authorized or ask to
    request.user = basic_auth(request)
    if request.user is None:
        return ask_basic_auth(request)
    print request.user

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

@render_to('projector/project/list.html')
def project_list(request):
    project_list = Project.objects.projects_for_user(user=request.user)\
        .annotate(Count('task'))
    context = {
        'project_list' : project_list,
    }
    return context

def project_task_list(request, project_slug,
        template_name='projector/project/task_list.html'):
    project = Project.objects.get(slug=project_slug)
    if project.is_private():
        check = ProjectPermission(request.user)
        if not check.has_perm('project_permission.view_tasks_project',
            project):
            raise PermissionDenied()

    task_list = Task.objects.filter(project__id=project.id)\
            .select_related('priority', 'status', 'author', 'project')
    filters = TaskFilter(request.GET,
        queryset=task_list, project=project)
    if request.GET and 'id' in request.GET and request.GET['id'] and \
        filters.qs.count() == 1:
        task = filters.qs[0]
        messages.info(request, _("One task matched - redirecting..."))
        return redirect(task.get_absolute_url())
    context = {
        'project': project,
        'filters': filters,
    }
    return render_to_response(template_name, context, RequestContext(request))

@login_required
@render_to('projector/project/create.html')
def project_create(request):
    """
    New project creation view.
    """
    project = Project(
        author=request.user,
    )
    form = ProjectForm(request.POST or None, instance=project)
    if request.method == 'POST' and form.is_valid():
        project = form.save()
        project.create_workflow()
        return HttpResponseRedirect(project.get_absolute_url())
    context = {
        'form' : form,
    }

    return context

@permission_required_or_403('project_permission.change_project',
    (Project, 'slug', 'project_slug'))
@render_to('projector/project/edit.html')
def project_edit(request, project_slug):
    """
    Update project view.
    """
    project = get_object_or_404(Project, slug=project_slug)
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

@render_to('projector/project/milestone_list.html')
def project_milestones(request, project_slug):
    """
    Returns milestones view.
    """
    project = get_object_or_404(Project, slug=project_slug)
    if project.is_private():
        check = ProjectPermission(user=request.user)
        if not check.view_project(project):
            raise PermissionDenied()
    milestone_list = project.milestone_set\
        .annotate(Count('task'))
    context = {
        'project': project,
        'milestone_list': milestone_list,
    }
    return context

@render_to('projector/project/milestone_detail.html')
def project_milestone_detail(request, project_slug, milestone_slug):
    """
    Returns milestone detail view.
    """
    project = get_object_or_404(Project, slug=project_slug)
    milestone = get_object_or_404(Milestone,
        project=project, slug=milestone_slug)
    if project.is_private():
        check = ProjectPermission(user=request.user)
        if not check.view_project(project):
            raise PermissionDenied()
    context = {
        'project': project,
        'milestone': milestone,
    }
    return context

@permission_required_or_403('project_permission.change_project',
    (Project, 'slug', 'project_slug'))
@render_to('projector/project/milestone_add.html')
def project_milestones_add(request, project_slug):
    """
    Adds milestone for project.
    """
    project = get_object_or_404(Project, slug=project_slug)
    milestone = Milestone(project=project, author=request.user)
    form = MilestoneForm(request.POST or None, instance=milestone)
    if request.method == 'POST' and form.is_valid():
        milestone = form.save()
        msg = _("Milestone added successfully")
        messages.success(request, msg)
        return redirect(milestone.get_absolute_url())
    context = {
        'form': form,
        'project': project,
    }
    return context

@permission_required_or_403('project_permission.change_project',
    (Project, 'slug', 'project_slug'))
@render_to('projector/project/milestone_edit.html')
def project_milestone_edit(request, project_slug, milestone_slug):
    """
    Edits chosen milestone.
    """
    project = get_object_or_404(Project, slug=project_slug)
    milestone = get_object_or_404(Milestone, slug=milestone_slug)
    form = MilestoneForm(request.POST or None, instance=milestone)
    if request.method == 'POST' and form.is_valid():
        milestone = form.save()
        msg = _("Milestone updated successfully")
        messages.success(request, msg)
        return redirect(milestone.get_absolute_url())
    context = {
        'form': form,
        'project': project,
    }
    return context

@render_to('projector/project/component_list.html')
def project_components(request, project_slug):
    """
    Returns components view.
    """
    project = get_object_or_404(Project, slug=project_slug)
    if project.is_private():
        check = ProjectPermission(user=request.user)
        if not check.view_project(project):
            raise PermissionDenied()
    component_list = project.component_set\
        .annotate(Count('task'))
    context = {
        'project': project,
        'component_list': component_list,
    }
    return context

@render_to('projector/project/component_detail.html')
def project_component_detail(request, project_slug, component_slug):
    """
    Returns component detail view.
    """
    project = get_object_or_404(Project, slug=project_slug)
    component = get_object_or_404(Component, project=project,
        slug=component_slug)
    if project.is_private():
        check = ProjectPermission(user=request.user)
        if not check.view_project(project):
            raise PermissionDenied()
    context = {
        'project': project,
        'component': component,
    }
    return context

@permission_required_or_403('project_permission.change_project',
    (Project, 'slug', 'project_slug'))
@render_to('projector/project/component_add.html')
def project_component_add(request, project_slug):
    """
    Adds component for project.
    """
    project = get_object_or_404(Project, slug=project_slug)
    component = Component(project=project)
    form = ComponentForm(request.POST or None, instance=component)
    if request.method == 'POST' and form.is_valid():
        component = form.save()
        msg = _("Component added successfully")
        messages.success(request, msg)
        return redirect(component.get_absolute_url())
    context = {
        'form': form,
        'project': project,
    }
    return context

@permission_required_or_403('project_permission.change_project',
    (Project, 'slug', 'project_slug'))
@render_to('projector/project/component_edit.html')
def project_component_edit(request, project_slug, component_slug):
    """
    Edits chosen component.
    """
    project = get_object_or_404(Project, slug=project_slug)
    component = get_object_or_404(Component,
        project=project, slug=component_slug)
    form = ComponentForm(request.POST or None, instance=component)
    if request.method == 'POST' and form.is_valid():
        component = form.save()
        msg = _("Milestone updated successfully")
        messages.success(request, msg)
        return redirect(component.get_absolute_url())
    context = {
        'form': form,
        'project': project,
    }
    return context

@render_to('projector/project/workflow_detail.html')
def project_workflow_detail(request, project_slug):
    """
    Returns project's workflow detail view.
    """
    project = get_object_or_404(Project, slug=project_slug)
    if project.is_private():
        check = ProjectPermission(user=request.user)
        if not check.view_project(project):
            raise PermissionDenied()
    context = {
        'project': project,
    }
    return context

@permission_required_or_403('project_permission.change_project',
    (Project, 'slug', 'project_slug'))
@render_to('projector/project/workflow_edit.html')
def project_workflow_edit(request, project_slug):
    """
    Edits chosen project's workflow.
    """
    project = get_object_or_404(Project, slug=project_slug)
    formset = StatusFormSet(request.POST or None,
        queryset=Status.objects.filter(project=project))
    if request.method == 'POST':
        if formset.is_valid():
            msg = _("Workflow updated successfully")
            messages.success(request, msg)
            for form in formset.forms:
                # update status instance
                form.instance.save()
                destinations = form.cleaned_data['destinations']
                # remove unchecked
                Transition.objects.filter(~Q(destination__in=destinations),
                    source=form.instance)\
                    .delete()
                # add new
                for destination in destinations:
                    Transition.objects.get_or_create(source=form.instance,
                        destination=destination)
        else:
            msg = _("Errors occured while processing formset")
            messages.error(request, msg)
    context = {
        'formset': formset,
        'project': project,
    }
    return context

@permission_required_or_403('project_permission.change_project',
    (Project, 'slug', 'project_slug'))
@render_to('projector/project/workflow_add_status.html')
def project_workflow_add_status(request, project_slug):
    """
    Adds status for project.
    """
    project = get_object_or_404(Project, slug=project_slug)
    _max_order_status = get_first_or_None(
        project.status_set.only('order').order_by('-order'))
    status = Status(project=project,
        order=_max_order_status and _max_order_status.order+1 or 1)
    form = StatusForm(request.POST or None, instance=status)
    if request.method == 'POST' and form.is_valid():
        form.save()
        msg = _("Status added successfully")
        messages.success(request, msg)
        return redirect(project.get_workflow_url())
    context = {
        'form': form,
        'project': project,
    }
    return context

# ========================== #
# Membership - user & groups #
# ========================== #

# Members

def project_members(request, project_slug,
        template_name='projector/project/members.html'):
    """
    Shows/updates project's members and groups view.
    """
    project = get_object_or_404(Project, slug=project_slug)
    if project.is_private():
        check = ProjectPermission(request.user)
        if not check.has_perm('project_permission.view_members_project',
            project):
            raise PermissionDenied()
    memberships = Membership.objects.filter(project=project)

    context = {
        'project': project,
        'memberships': memberships,
    }
    return render_to_response(template_name, context, RequestContext(request))

@permission_required_or_403('project_permission.add_member_project',
    (Project, 'slug', 'project_slug'))
def project_members_add(request, project_slug,
        template_name='projector/project/members_add.html'):
    """
    Adds member for a project.
    """
    project = get_object_or_404(Project, slug=project_slug)
    membership = Membership(
        project = project,
    )
    form = MembershipForm(request.POST or None, instance=membership)

    if request.method == 'POST' and form.is_valid():
        logging.info("Saving member %s for project '%s'"
            % (form.instance.member, form.instance.project))
        form.save()
        return redirect(project.get_members_url())
    elif form.errors:
        logging.error("Form contains errors:\n%s" % form.errors)

    context = {
        'project': form.instance.project,
        'form': form,
    }
    return render_to_response(template_name, context, RequestContext(request))

@permission_required_or_403('project_permission.change_member_project',
    (Project, 'slug', 'project_slug'))
@render_to('projector/project/members_manage.html')
def project_members_manage(request, project_slug, username):
    """
    Manages membership settings and permissions of project's member.
    """
    membership = get_object_or_404(Membership,
        project__slug=project_slug, member__username=username)
    member = membership.member
    project = membership.project
    if not request.user.is_superuser and project.author == member:
        # allow if requested by superuser
        messages.warning(request, _("Project owner's membership cannot be "
            "modified. He/She has all permissions for this project."))
        return redirect(project.get_members_url())
    check = ProjectPermission(user=member)

    form = MembershipForm(request.POST or None, instance=membership)
    permissions = ProjectPermission(membership.member)
    available_permissions = [ '.'.join(('project_permission', perm))
        for perm in permissions.checks if perm.endswith('_project')]
    logging.info("Available permissions for projects are:\n%s"
        % pprint.pformat(available_permissions))

    # Fetch members' permissions for this project
    member_current_permissions = member\
        .granted_permissions\
        .get_for_model(project)\
        .select_related('user', 'creator', 'group', 'content_type')\
        .filter(object_id=project.id)

    def get_or_create_permisson(perm):
        for perm_obj in member_current_permissions:
            if perm_obj.codename == perm:
                return perm_obj
        perm_obj, created = Permission.objects.get_or_create(
            creator = request.user,
            content_type = ContentType.objects.get_for_model(
                membership.project),
            object_id = membership.project.id,
            codename = perm,
            user = membership.member,
            approved = False,
        )
        return perm_obj

    logging.info("Current %s's permissions:" % member)
    for perm in member_current_permissions:
        logging.info("%s | Approved is %s" % (perm, perm.approved))

    if request.method == 'POST':
        granted_perms = request.POST.getlist('perms')
        logging.debug("POST'ed perms: %s" % granted_perms)
        for perm in available_permissions:
            logging.info("Permisson %s | Member %s has it: %s"
                % (perm, member, member.has_perm(perm)))
            if perm in granted_perms and not check.has_perm(perm, project):
                # Grant perm
                logging.debug("Granting permission %s for user %s"
                    % (perm, member))
                perm_obj = get_or_create_permisson(perm)
                if not perm_obj.approved:
                    perm_obj.approved = True
                    perm_obj.save()
            if perm not in granted_perms and check.has_perm(perm, project):
                # Disable perm
                logging.debug("Disabling permission %s for user %s"
                    % (perm, member))
                perm_obj = get_or_create_permisson(perm)
                perm_obj.approved = False
                perm_obj.creator = request.user
                perm_obj.save()

    context = {
        'project': project,
        'form': form,
        'membership': membership,
        'permissions': permissions,
        'available_permissions': available_permissions,
    }
    return context

# Teams

def project_teams(request, project_slug,
        template_name='projector/project/teams/home.html'):
    """
    Shows/updates project's teams view.
    """
    project = get_object_or_404(Project, slug=project_slug)
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
    (Project, 'slug', 'project_slug'))
def project_teams_add(request, project_slug,
        template_name='projector/project/teams/create.html'):
    """
    Adds team for a project.
    """
    project = get_object_or_404(Project, slug=project_slug)
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
    (Project, 'slug', 'project_slug'))
def project_teams_manage(request, project_slug, name,
        template_name='projector/project/teams/edit.html'):
    """
    Manages settings and permissions of project's team.
    """
    team = get_object_or_404(Team,
        project__slug=project_slug, group__name=name)
    project = team.project
    group = team.group
    check = ProjectPermission(group=team.group)

    form = TeamForm(request.POST or None, instance=team)
    available_permissions = check.get_local_checks()
    logging.info("Available permissions for projects are:\n%s"
        % pprint.pformat(available_permissions))

    logging.info("Current %s's permissions:" % group)
    for perm in team.perms:
        logging.info("%s | Approved is %s" % (perm, perm.approved))

    team_short_perms = [perm.codename.split('.')[-1] for perm in team.perms]

    if request.method == 'POST':
        granted_perms = request.POST.getlist('perms')
        logging.debug("POST'ed perms: %s" % granted_perms)
        for perm in available_permissions:
            logging.info("Permisson %s | Team %s has it: %s"
                % (perm, team, perm in team.perms))
            perm_codename = '.'.join((check.label, perm))
            if perm in granted_perms and not perm in team_short_perms:
                # Grant perm
                logging.debug("Granting permission %s for team %s"
                    % (perm_codename, team))
                get_or_create_permisson(
                    perm_codename,
                    project,
                    group = team.group,
                    approved = True,
                    creator = request.user,
                )
            if perm not in granted_perms and perm in team_short_perms:
                # Disable perm
                logging.debug("Disabling permission %s for team %s"
                    % (perm_codename, team))
                try:
                    team.perms.get(codename=perm_codename).delete()
                except Permission.DoesNotExist:
                    pass
        return redirect(team.get_absolute_url())

    context = {
        'project': project,
        'form': form,
        'team': team,
        'available_permissions': available_permissions,
        'team_short_perms': team_short_perms,
    }
    return render_to_response(template_name, context, RequestContext(request))


def project_browse_repository(request, project_slug, rel_repo_url='',
        revision='tip', template_name='projector/project/repository.html'):
    """
    Handles project's repository browser.
    """
    project = get_object_or_404(Project, slug=project_slug)
    if project.is_private():
        check = ProjectPermission(request.user)
        if not request.user.is_authenticated() or \
            not check.read_repository_project(project):
            raise PermissionDenied()
    if not project._get_repo_path():
        messages.error(request, _("Repository's url is not set! Please "
            "configure project preferences first."))
    repo_info = {
        'repository': project.repository,
        'revision': revision,
        'node_path': rel_repo_url,
        'template_name': template_name,
        'extra_context': {
            'project': project,
        },
    }
    return browse_repository(request, **repo_info)

@render_to('projector/project/changeset_list.html')
def project_changesets(request, project_slug):
    """
    Returns repository's changesets view.
    """
    project = get_object_or_404(Project, slug=project_slug)
    if project.is_private():
        check = ProjectPermission(request.user)
        if not check.read_repository_project(project):
            raise PermissionDenied()
    if not project._get_repo_path():
        messages.error(request, _("Repository's url is not set! Please "
            "configure project preferences first."))
    context = {
        'project': project,
    }
    context['repository'] = project.repository
    return context

