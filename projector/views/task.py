import datetime
import pprint
import logging
import django_filters

from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.views.generic import list_detail
from django.forms.formsets import formset_factory
from django import forms
from django.contrib import messages
from django.utils.translation import ugettext as _

from authority.decorators import permission_required_or_403

from projector.models import Task, Status, Priority, Project
from projector.forms import TaskForm, TaskEditForm, TaskCommentForm
from projector.permissions import ProjectPermission

from richtemplates.shortcuts import get_first_or_None
from richtemplates.forms import DynamicActionChoice, DynamicActionFormFactory,\
    UserByNameField

def task_details(request, project_slug, task_id, template_name='projector/task/details.html'):
    """
    Task details view.
    Users may update task here.
    """
    task = get_object_or_404(
        Task.objects.select_related('type', 'priority', 'status', 'owner',
            'author', 'editor', 'milestone', 'component', 'project'),
        id=task_id, project__slug=project_slug)
        
    # We create formset for comment here as comment is only optional
    CommentFormset = formset_factory(TaskCommentForm, extra=1)

    check = ProjectPermission(request.user)
    destinations = task.status.destinations.all()
    # Init choices
    task_action_choices = [
        DynamicActionChoice(0, _("Don't change status")),
    ]
    if check.change_task_project(task.project):
        if destinations:
            task_action_choices.append(DynamicActionChoice(1, _("Change status"),
                {'new_status': forms.ModelChoiceField(
                    queryset=destinations.exclude(id=task.status.id),
                    empty_label=None)
                }))

    TaskActionForm = DynamicActionFormFactory(task_action_choices)
    action_form = TaskActionForm(request.POST or None, request.FILES or None)

    comment_formset = CommentFormset(request.POST or None)
    if request.method == 'POST':

        if action_form.is_valid() and comment_formset.is_valid():
            # Comment handler
            comment_form = comment_formset.forms[0]
            if comment_form.cleaned_data.has_key('comment'):
                comment = comment_form.cleaned_data['comment']
            else:
                comment = None
            # Task handler
            data = action_form.cleaned_data
            task.editor = request.user
            task.editor_ip = request.META['REMOTE_ADDR']
            # action_type number as defined before at DynamicActionChoices
            action_type = data['action_type']
            if check.change_task_project(task.project):
                if action_type == 1:
                    task.status = data['new_status']
            if action_type > 0 or comment:
                messages.success(request, _("Task updated successfully"))
                task.save()
                task.create_revision(comment)
            else:
                messages.warning(request, _("There were no changes"))
            return HttpResponseRedirect(task.get_absolute_url())
        else:
            logging.error(action_form.errors)
    
    context = {
        'task' : task,
        'now' : datetime.datetime.now(),
        'action_form' : action_form,
        'comment_formset' : comment_formset,
    }

    return render_to_response(template_name, context, RequestContext(request))

@permission_required_or_403('project_permission.add_task_project',
    (Project, 'slug', 'project_slug'))
def task_create(request, project_slug, template_name='projector/task/create.html'):
    """
    New Task creation view.
    """
    project = get_object_or_404(Project, slug=project_slug)
    if project.is_private():
        check = ProjectPermission(request.user)
        if not check.add_task_project(project):
            raise PermissionDenied()
    initial = {
        'owner': request.user.username, # form's owner is UserByNameField
    }
    status = get_first_or_None(project.status_set)
    type = get_first_or_None(project.tasktype_set)
    priority = get_first_or_None(project.priority_set)
    component = get_first_or_None(project.component_set)

    for attr in (status, type, priority, component):
        if attr is None:
            messages.error(request, _("Statuses, task types, priorities or "
                "components of this project are missing and we "
                "cannot create new tasks. Ask site administrator for "
                "help."))
            return render_to_response(template_name, {}, RequestContext(request))

    instance = Task(
        project=project,
        author = request.user,
        author_ip = request.META['REMOTE_ADDR'],
        editor = request.user,
        editor_ip = request.META['REMOTE_ADDR'],
        status = status,
        type = type,
        priority = priority,
        component = component,
    )
    form = TaskForm(request.POST or None, initial=initial, instance=instance)
    if request.method == 'POST':
        if form.errors:
            logging.error("Form has following errors:\n%s" % pprint.pformat(form.errors))
        if form.is_valid():
            task = form.save(
                editor = request.user,
                editor_ip = request.META['REMOTE_ADDR'],
                #project = project,
            )
            task.create_revision()
            messages.success(request, _("Task created succesfully."))
            return HttpResponseRedirect(task.get_absolute_url())

    context = {
        'form' : form,
    }

    return render_to_response(template_name, context, RequestContext(request))

@permission_required_or_403('project_permission.change_task_project',
    (Project, 'slug', 'project_slug'))
def task_edit(request, project_slug, task_id, template_name='projector/task/create.html'):
    """
    Edit Task meta information. task_details edits the rest.
    """
    task = get_object_or_404(Task, id=task_id, project__slug=project_slug)

    if request.method == 'POST':
        form = TaskEditForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save(
                editor=request.user,
                editor_ip=request.META['REMOTE_ADDR'],
            )
            comment = form.cleaned_data.get('comment', None)
            task.create_revision(comment)
            messages.success(request, _("Task updated successfully."))
            return HttpResponseRedirect(task.get_absolute_url())
    else:
        form = TaskEditForm(instance=task, initial={
            'owner': task.owner and task.owner.username or None,
        })

    context = {
        'form' : form,
    }

    return render_to_response(template_name, context, RequestContext(request))

