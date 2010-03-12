import logging
import pprint

from django.conf import settings
from django.contrib import auth
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.utils.http import urlquote
from django.views.generic import list_detail, create_update

from annoying.decorators import render_to

from authority.decorators import permission_required_or_403
from authority.forms import UserPermissionForm
from authority.models import Permission

from projector.models import Project, ProjectCategory, Membership, Task
from projector.forms import ProjectForm, MembershipForm
from projector.views.task import task_create
from projector.permissions import ProjectPermission
from projector.utils.simplehg import hgrepo_detail, is_mercurial

from urlparse import urljoin

def project_details(request, project_slug, template_name='projector/project/details.html'):
    project = get_object_or_404(Project, slug=project_slug)
    if is_mercurial(request):
        return hgrepo_detail(request, project.slug)
    if not request.user.is_authenticated() and project.is_private():
        path = urlquote(request.get_full_path())
        tup = settings.LOGIN_URL, auth.REDIRECT_FIELD_NAME, path
        return HttpResponseRedirect('%s?%s=%s' % tup)
    
    context = {
        'project': project,
    }
    return render_to_response(template_name, context, RequestContext(request))

def project_task_list(request, project_slug, template_name='projector/project/task_list.html'):
    project = Project.objects.get(slug=project_slug)    
    if project.is_private():
        check = ProjectPermission(request.user)
        if not check.has_perm('project_permission.view_tasks_for_project',
            project):
            raise PermissionDenied()

    task_list = Task.objects.filter(project__id=project.id)\
            .select_related('priority', 'status', 'author', 'project')
            #.defer('project')
    context = {
        'project': project,
        'task_list': task_list,
    }
    #logging.info("Task list:\n%s" % task_list)
    return render_to_response(template_name, context, RequestContext(request))

@login_required
@permission_required('projector.add_project')
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
        project = form.save(commit=False)
        #project.author = request.user
        project.save()
        member = Membership.objects.create(project=project, member=request.user)
        return HttpResponseRedirect(project.get_absolute_url())
    
    context = {
        'form' : form,
    }

    return context

@login_required
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
        messages.success(request, "Project edited successfully.")
        return HttpResponseRedirect(project.get_absolute_url())

    context = {
        'form' : form,
        'project': form.instance,
    }

    return context

@render_to('projector/project/members.html')
def project_members(request, project_slug):
    """
    Shows/updates project's members view.
    """
    project = get_object_or_404(Project, slug=project_slug)
    memberships = Membership.objects\
        .filter(project=project)
    
    context = {
        'project': project,
        'memberships': memberships,
    }
    return context

@permission_required_or_403('project_permission.add_member_to_project',
    (Project, 'slug', 'project_slug'))
@render_to('projector/project/members_add.html')
def project_members_add(request, project_slug):
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
    return context

@permission_required_or_403('project_permission.add_member_to_project',
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

def project_list(request, template_name='projector/project/list.html'):
    project_queryset = Project.objects.projects_for_user(user=request.user)
    kwargs = {
        'queryset' : project_queryset.annotate(Count('task')),
        'template_name' : template_name,
        'template_object_name' : 'project',
    }
    return list_detail.object_list(request, **kwargs)

@render_to('projector/project/repository.html')
def project_browse_repository(request, project_slug, rel_repo_url):
    """
    Handles project's repository browser.
    """
    try:
        from vcbrowser import engine_from_url
        from vcbrowser.engine.base import VCBrowserError, EngineError
    except ImportError, err:
        messages.error(request, str(err))
        messages.info(request, "vcbrowser is available at "
            "http://code.google.com/p/python-vcbrowser/")
        return {}

    project = get_object_or_404(Project, slug=project_slug)
    if project.is_private():
        check = ProjectPermission(request.user)
        if not request.user.is_authenticated() or \
            not check.can_read_repository_project(project):
            raise PermissionDenied()


    if not project.repository_url:
        messages.error(request, _("Repository's url is not set! Please "
            "configure project preferences first."))
        #raise Http404

    context = {
        'project': project,
    }
    
    # Some custom logic here
    revision = request.GET.get('revision', None)

    try:
        engine = engine_from_url('hg://' + project.get_repo_path())
        requested_node = engine.request(rel_repo_url, revision, fetch_content=True)
        context['root'] = requested_node
    except VCBrowserError, err:
        messages.error(request, str(err))
    except EngineError, err:
        messages.error(request, str(err))
    return context

