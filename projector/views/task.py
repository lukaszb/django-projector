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
from projector.forms import TaskForm, TaskEditForm, TaskCommentForm, UserByNameField
from projector.permissions import ProjectPermission

from richtemplates.forms import DynamicActionChoice, DynamicActionFormFactory

def task_details(request, project_slug, task_id, template_name='projector/task/details.html'):
    """
    Task details view.
    Users may update task here.
    """
    logging.debug("task_details called")
    task = get_object_or_404(
        Task.objects.select_related('type', 'priority', 'status', 'owner',
            'author', 'editor', 'milestone', 'component', 'project'),
        id=task_id, project__slug=project_slug)
        
    # We create formset for comment here as comment is only optional
    CommentFormset = formset_factory(TaskCommentForm, extra=1)
    
    task_action_choices = [
        DynamicActionChoice(0, _("Don't change status")),
        DynamicActionChoice(2, _("Resolve to"),
            {
                'resolve_to' : forms.ModelChoiceField(
                    Status.objects.filter(is_resolved=True, project=task.project)),
            }),
        DynamicActionChoice(3, _("Assign to"),
            { 'assign_to' : UserByNameField(max_length=256) }),
        DynamicActionChoice(4, _("Reopen as"),
            {
                'reopen_as' : forms.ModelChoiceField(
                    Status.objects\
                            .filter(is_resolved=False, project=task.project)\
                            .exclude(name='assigned'),
                empty_label=None)
            }),
    ]
    if task.owner != request.user:
        task_action_choices.insert(1, DynamicActionChoice(1, _("Accept task")))
    
    enabled_choices = [0]
    if task.status.is_resolved:
        enabled_choices += [4]
    else:
        enabled_choices += [1,2,3]
    
    TaskActionForm = DynamicActionFormFactory(task_action_choices, enabled_choices)
    
    if request.method == 'POST':
        action_form = TaskActionForm(request.POST)
        comment_formset = CommentFormset(request.POST)

        if action_form.is_valid() and comment_formset.is_valid():
            task.editor = request.user
            task.editor_ip = request.META['REMOTE_ADDR']
            cleaned_data = action_form.cleaned_data
            action_type = cleaned_data['action_type']
            action = None

            # Accept task
            if action_type == 1:
                task.status = Status.objects.get(id=2)
                task.owner = request.user
                action = _("Accepted by") + " '%s'" % request.user.username
            # Resolve as ...
            if action_type == 2:
                task.status = cleaned_data['resolve_to']
                action = _("Resolved to") + " '%s'" % task.status.name
            # Assign to ...
            if action_type == 3:
                task.owner = cleaned_data['assign_to']
                action = _("Assigned to") + " '%s'" % task.owner.username
            # Reopen as ...
            if action_type == 4:
                task.status = cleaned_data['reopen_as']
                action = _("Reopened as") + " '%s'" % task.status.name
            
            
            if action:
                messages.success(request, action)
            else:
                messages.warning(request, _("Task hasn't been changed."))
            
            # Comment handler
            comment_form = comment_formset.forms[0]
            if comment_form.cleaned_data.has_key('comment'):
                comment = comment_form.cleaned_data['comment']
                from django.db import connection
                q = connection.queries
                #task.add_comment_to_current_revision(comment)
                logging.debug("Added comment to current revision")
                logging.debug("Query was: %s" % pprint.pformat(q[-1]))
                messages.success(request, _("Comment added successfully."))
            else:
                comment = None
            if action or comment:
                task.save()
                if comment:
                    task.add_comment_to_current_revision(comment)
            return HttpResponseRedirect(task.get_absolute_url())
        else:
            logging.error(action_form.errors)
    else:
        action_form = TaskActionForm()
        comment_formset = CommentFormset()
    
    status_list = Status.objects.order_by('order')
    resolve_status_list = status_list.filter(is_resolved=True)
    reopen_status_list = status_list.filter(is_resolved=False)
    
    context = {
        'task' : task,
        'now' : datetime.datetime.now(),
        'action_form' : action_form,
        'comment_formset' : comment_formset,
        'resolve_status_list' : resolve_status_list,
        'reopen_status_list' : reopen_status_list,
    }

    return render_to_response(template_name, context, RequestContext(request))

@permission_required_or_403('project_permission.add_task_project',
    (Project, 'slug', 'project_slug'))
def task_create(request, project_slug, template_name='projector/task/create.html'):
    """
    New Task creation view.
    """
    logging.debug("task_create called")
    project = get_object_or_404(Project, slug=project_slug)
    if project.is_private():
        check = ProjectPermission(request.user)
        if not check.add_task_project(project):
            raise PermissionDenied()
    initial = {
        'owner': request.user.username, # form's owner is UserByNameField
    }
    instance = Task(
        project=project,
        author = request.user,
        author_ip = request.META['REMOTE_ADDR'],
        editor = request.user,
        editor_ip = request.META['REMOTE_ADDR'],
        status = project.status_set.get(order=1),
        type = project.tasktype_set.get(order=1),
        priority = project.priority_set.get(order=1),
        component = project.projectcomponent_set.all()[0],
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
    logging.debug("task_edit called")
    task = get_object_or_404(Task, id=task_id, project__slug=project_slug)

    if request.method == 'POST':
        form = TaskEditForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save(
                editor=request.user,
                editor_ip=request.META['REMOTE_ADDR'],
            )
            if 'comment' in form.cleaned_data:
                comment = form.cleaned_data['comment']
                task.add_comment_to_current_revision(comment)
            messages.success(request, _("Task updated successfully."))
            return HttpResponseRedirect(task.get_absolute_url())
    else:
        form = TaskEditForm(instance=task, initial={
            'owner': task.owner.username,
        })

    context = {
        'form' : form,
    }

    return render_to_response(template_name, context, RequestContext(request))

