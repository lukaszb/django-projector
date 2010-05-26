import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.util import NestedObjects
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.utils.translation import ugettext as _

from authority.decorators import permission_required_or_403

from livesettings import config_value

from projector.models import Project, Membership, Team, Task
from projector.models import Milestone, Status, Transition, Component
from projector.forms import ProjectForm, MembershipForm, MilestoneForm
from projector.forms import MembershipDeleteForm
from projector.forms import StatusForm, StatusFormSet, ComponentForm
from projector.forms import TeamForm, ProjectMembershipPermissionsForm,\
    ProjectTeamPermissionsForm
from projector.permissions import ProjectPermission, get_perms_for_user
from projector.filters import TaskFilter

from richtemplates.shortcuts import get_first_or_None

from vcs.web.simplevcs import settings as simplevcs_settings
from vcs.web.simplevcs.utils import get_mercurial_response, is_mercurial
from vcs.web.simplevcs.utils import log_error, basic_auth, ask_basic_auth
from vcs.web.simplevcs.exceptions import NotMercurialRequest
from vcs.web.simplevcs.views import browse_repository, diff_file

def project_details(request, username, project_slug,
        template_name='projector/project/details.html'):
    """
    Returns selected project's detail for user given in ``request``.
    We make necessary permission checks *after* dispatching between
    normal and mercurial request, as mercurial requests has it's own
    permission requirements.
    """
    try:
        project = get_object_or_404(Project, slug=project_slug,
            author__username=username)
        if is_mercurial(request):
            return _project_detail_hg(request, project)
        last_part = request.path.split('/')[-1]
        if last_part and last_part != project_slug:
            raise Http404("Not a mercurial request and path longer than should "
                "be: %s" % request.path)
        if project.is_private():
            check = ProjectPermission(user=request.user)
            if not check.has_perm('project_permission.view_project', project):
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
    if not is_mercurial(request):
        msg = "_project_detail_hg called for non mercurial request"
        logging.error(msg)
        raise NotMercurialRequest(msg)

    if request.method not in ('GET', 'POST'):
        raise NotMercurialRequest("Only GET/POST methods are allowed, got %s"
            % request.method)
    # Allow to read from public projects
    if project.is_public() and request.method == 'GET' and \
        config_value('PROJECTOR', 'ALWAYS_ALLOW_READ_PUBLIC_PROJECTS'):
        mercurial_info = {
            'repo_path': project._get_repo_path(),
            'push_ssl': simplevcs_settings.PUSH_SSL,
        }
        return get_mercurial_response(request, **mercurial_info)

    # Check if user have been already authorized or ask to
    request.user = basic_auth(request)
    if request.user is None:
        return ask_basic_auth(request, realm=config_value('PROJECTOR',
            'BASIC_AUTH_REALM'))

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

def project_list(request, template_name='projector/project/list.html'):
    project_list = Project.objects.for_user(user=request.user)\
        .annotate(Count('task', distinct=True))
    context = {
        'project_list' : project_list,
    }
    return render_to_response(template_name, context, RequestContext(request))

def project_task_list(request, username, project_slug,
        template_name='projector/project/task_list.html'):
    project = get_object_or_404(Project, slug=project_slug,
        author__username=username)
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
def project_create(request, username,
        template_name='projector/project/create.html'):
    """
    New project creation view.
    """
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

    return render_to_response(template_name, context, RequestContext(request))

@permission_required_or_403('project_permission.change_project',
    (Project, 'author__username', 'username'),
    (Project, 'slug', 'project_slug'))
def project_edit(request, username, project_slug,
        template_name='projector/project/edit.html'):
    """
    Update project view.
    """
    project = get_object_or_404(Project, slug=project_slug,
        author__username=username)
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

    return render_to_response(template_name, context, RequestContext(request))

def project_milestones(request, username, project_slug,
        template_name='projector/project/milestones/home.html'):
    """
    Returns milestones view.
    """
    project = get_object_or_404(Project, slug=project_slug,
        author__username=username)
    if project.is_private():
        check = ProjectPermission(user=request.user)
        if not check.view_project(project):
            raise PermissionDenied()
    milestone_list = project.milestone_set\
        .annotate(Count('task'))\
        .order_by('-created_at')
    context = {
        'project': project,
        'milestone_list': milestone_list,
    }
    return render_to_response(template_name, context, RequestContext(request))

def project_milestone_detail(request, username, project_slug, milestone_slug,
        template_name='projector/project/milestones/detail.html'):
    """
    Returns milestone detail view.
    """
    project = get_object_or_404(Project, slug=project_slug,
        author__username=username)
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
    return render_to_response(template_name, context, RequestContext(request))

@permission_required_or_403('project_permission.change_project',
    (Project, 'slug', 'project_slug'),
    (Project, 'author__username', 'username'))
def project_milestones_add(request, username, project_slug,
        template_name='projector/project/milestones/add.html'):
    """
    Adds milestone for project.
    """
    project = get_object_or_404(Project, slug=project_slug,
        author__username=username)
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
    return render_to_response(template_name, context, RequestContext(request))

@permission_required_or_403('project_permission.change_project',
    (Project, 'slug', 'project_slug'),
    (Project, 'author__username', 'username'))
def project_milestone_edit(request, username, project_slug, milestone_slug,
        template_name='projector/project/milestones/edit.html'):
    """
    Edits chosen milestone.
    """
    project = get_object_or_404(Project, slug=project_slug,
        author__username=username)
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
    return render_to_response(template_name, context, RequestContext(request))

def project_components(request, username, project_slug,
        template_name='projector/project/components/home.html'):
    """
    Returns components view.
    """
    project = get_object_or_404(Project, slug=project_slug,
        author__username=username)
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
    return render_to_response(template_name, context, RequestContext(request))

def project_component_detail(request, username, project_slug, component_slug,
        template_name='projector/project/components/detail.html'):
    """
    Returns component detail view.
    """
    project = get_object_or_404(Project, slug=project_slug,
        author__username=username)
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
    return render_to_response(template_name, context, RequestContext(request))

@permission_required_or_403('project_permission.change_project',
    (Project, 'slug', 'project_slug'),
    (Project, 'author__username', 'username'))
def project_component_add(request, username, project_slug,
        template_name='projector/project/components/add.html'):
    """
    Adds component for project.
    """
    project = get_object_or_404(Project, slug=project_slug,
        author__username=username)
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
    return render_to_response(template_name, context, RequestContext(request))

@permission_required_or_403('project_permission.change_project',
    (Project, 'slug', 'project_slug'),
    (Project, 'author__username', 'username'))
def project_component_edit(request, username, project_slug, component_slug,
        template_name='projector/project/components/edit.html'):
    """
    Edits chosen component.
    """
    project = get_object_or_404(Project, slug=project_slug,
        author__username=username)
    component = get_object_or_404(Component,
        project=project, slug=component_slug)
    form = ComponentForm(request.POST or None, instance=component)
    if request.method == 'POST' and form.is_valid():
        component = form.save()
        msg = _("Component updated successfully")
        messages.success(request, msg)
        return redirect(component.get_absolute_url())
    context = {
        'form': form,
        'project': project,
    }
    return render_to_response(template_name, context, RequestContext(request))

def project_workflow_detail(request, username, project_slug,
        template_name='projector/project/workflow/detail.html'):
    """
    Returns project's workflow detail view.
    """
    project = get_object_or_404(Project, slug=project_slug,
        author__username=username)
    if project.is_private():
        check = ProjectPermission(user=request.user)
        if not check.view_project(project):
            raise PermissionDenied()
    context = {
        'project': project,
        # indicates that this is workflow detail page at templates
        'workflow': True,
    }
    return render_to_response(template_name, context, RequestContext(request))

@permission_required_or_403('project_permission.change_project',
    (Project, 'slug', 'project_slug'),
    (Project, 'author__username', 'username'))
def project_workflow_edit(request, username, project_slug,
        template_name='projector/project/workflow/edit.html'):
    """
    Edits chosen project's workflow.
    """
    project = get_object_or_404(Project, slug=project_slug,
        author__username=username)
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
    return render_to_response(template_name, context, RequestContext(request))

@permission_required_or_403('project_permission.change_project',
    (Project, 'slug', 'project_slug'),
    (Project, 'author__username', 'username'))
def project_workflow_add_status(request, username, project_slug,
        template_name='projector/project/workflow/add_status.html'):
    """
    Adds status for project.
    """
    project = get_object_or_404(Project, slug=project_slug,
        author__username=username)
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
    return render_to_response(template_name, context, RequestContext(request))

# ========================== #
# Membership - user & groups #
# ========================== #

# Members

def project_members(request, username, project_slug,
        template_name='projector/project/members/home.html'):
    """
    Shows/updates project's members and groups view.
    """
    project = get_object_or_404(Project, slug=project_slug,
        author__username=username)
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
    (Project, 'slug', 'project_slug'),
    (Project, 'author__username', 'username'))
def project_members_add(request, username, project_slug,
        template_name='projector/project/members/add.html'):
    """
    Adds member for a project.
    """
    project = get_object_or_404(Project, slug=project_slug,
        author__username=username)
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
    (Project, 'slug', 'project_slug'),
    (Project, 'author__username', 'username'))
def project_members_edit(request, username, project_slug, member_username,
        template_name='projector/project/members/edit.html'):
    """
    Manages membership settings and permissions of project's member.
    """
    membership = get_object_or_404(Membership, project__slug=project_slug,
        project__author__username=username, member__username=username)
    member = membership.member
    project = membership.project
    if not request.user.is_superuser and project.author == member:
        # allow if requested by superuser
        messages.warning(request, _("Project owner's membership cannot be "
            "modified. He/She has all permissions for this project."))
        return redirect(project.get_members_url())
    member_permissions = membership.all_perms
    codenames = [str(p.codename) for p in member_permissions]

    form = ProjectMembershipPermissionsForm(request.POST or None,
        membership = membership,
        initial_permissions = codenames,
        request = request)
    if request.method == 'POST':
        if form.is_valid():
            logging.info("Form's data:\n%s" % form.cleaned_data)
            messages.success(request, _("Permissions updated"))
            form.save()
        else:
            messages.error(request,
                _("Errors occured while processing the form"))
        return redirect(membership.get_absolute_url())
    context = {
        'project': project,
        'form': form,
        'membership': membership,
        'member_permissions': member_permissions,
    }
    return render_to_response(template_name, context, RequestContext(request))

@permission_required_or_403('project_permission.delete_member_project',
    (Project, 'slug', 'project_slug'),
    (Project, 'author__username', 'username'))
def project_members_delete(request, username, project_slug, member_username,
        template_name='projector/project/members/delete.html'):
    """
    Removes member from project.
    """
    membership = get_object_or_404(Membership, project__slug=project_slug,
        project__author__username=username, member__username=username)
    member = membership.member
    project = membership.project

    if project.author == member and not request.user.is_superuser:
        messages.warning(request, _("Project owner's membership cannot be "
            "removed."))
        return redirect(project.get_members_url())
    collector = NestedObjects()
    membership._collect_sub_objects(collector)
    form = MembershipDeleteForm(request.POST or None)
    perms_to_delete = get_perms_for_user(member, project)

    if request.method == 'POST':
        # Confirm removal
        if form.is_valid():
            msg = _("Membership removed")
            messages.success(request, msg)
            membership.delete()
            perms_to_delete.update(approved=False)
            return redirect(project.get_members_url())
        else:
            msg = _("Couldn't remove membership")
            messages.error(request, msg)
    context = {
        'project': project,
        'membership': membership,
        'form': form,
        'to_delete': collector.nested(),
        'perms_to_delete': perms_to_delete,
    }

    return render_to_response(template_name, context, RequestContext(request))


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
    (Project, 'slug', 'project_slug'),
    (Project, 'author__username', 'username'))
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
    (Project, 'slug', 'project_slug'),
    (Project, 'author__username', 'username'))
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


def project_browse_repository(request, username, project_slug, rel_repo_url='',
        revision='tip',
        template_name='projector/project/repository/browse.html'):
    """
    Handles project's repository browser.
    """
    project = get_object_or_404(Project, slug=project_slug,
        author__username=username)
    if project.is_private() or \
            not config_value('PROJECTOR', 'ALWAYS_ALLOW_READ_PUBLIC_PROJECTS'):
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

def project_file_diff(request, username, project_slug, revision_old,
        revision_new, rel_repo_url,
        template_name='projector/project/repository/diff.html'):
    """
    Returns diff page of the file at given ``rel_repo_url``.
    """
    project = get_object_or_404(Project, slug=project_slug,
        author__username=username)
    if project.is_private() or \
            not config_value('PROJECTOR', 'ALWAYS_ALLOW_READ_PUBLIC_PROJECTS'):
        check = ProjectPermission(request.user)
        if not request.user.is_authenticated() or \
            not check.read_repository_project(project):
            raise PermissionDenied()
    if not project._get_repo_path():
        messages.error(request, _("Repository's url is not set! Please "
            "configure project preferences first."))
    diff_info = {
        'repository': project.repository,
        'revision_old': revision_old,
        'revision_new': revision_new,
        'file_path': rel_repo_url,
        'template_name': template_name,
        'extra_context': {
            'project': project,
        },
    }
    return diff_file(request, **diff_info)

def project_file_raw(request, username, project_slug, revision, rel_repo_url):
    """
    Returns raw page of the file at given ``rel_repo_url``.
    """
    project = get_object_or_404(Project, slug=project_slug,
        author__username=username)
    if project.is_private() or \
            not config_value('PROJECTOR', 'ALWAYS_ALLOW_READ_PUBLIC_PROJECTS'):
        check = ProjectPermission(request.user)
        if not request.user.is_authenticated() or \
            not check.read_repository_project(project):
            raise PermissionDenied()
    node = project.repository.request(rel_repo_url, revision)
    response = HttpResponse(node.content, mimetype=node.mimetype)
    response['Content-Disposition'] = 'attachment; filename=%s' % node.name
    return response

def project_file_annotate(request, username, project_slug, revision,
        rel_repo_url,
        template_name='projector/project/repository/annotate.html'):
    """
    Returns raw page of the file at given ``rel_repo_url``.
    """
    project = get_object_or_404(Project, slug=project_slug,
        author__username=username)
    if project.is_private() or \
            not config_value('PROJECTOR', 'ALWAYS_ALLOW_READ_PUBLIC_PROJECTS'):
        check = ProjectPermission(request.user)
        if not request.user.is_authenticated() or \
            not check.read_repository_project(project):
            raise PermissionDenied()
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

def project_changesets(request, username, project_slug,
        template_name='projector/project/repository/changeset_list.html'):
    """
    Returns repository's changesets view.
    """
    project = get_object_or_404(Project, slug=project_slug,
        author__username=username)
    if project.is_private() or \
            not config_value('PROJECTOR', 'ALWAYS_ALLOW_READ_PUBLIC_PROJECTS'):
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
    context['CHANGESETS_PAGINATE_BY'] = config_value('PROJECTOR',
        'CHANGESETS_PAGINATE_BY')
    return render_to_response(template_name, context, RequestContext(request))

