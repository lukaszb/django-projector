import datetime
import logging

from django import forms
from django.shortcuts import get_object_or_404, redirect
from django.core.exceptions import PermissionDenied
from django.forms.formsets import formset_factory
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator

from projector.models import Task
from projector.forms import TaskForm, TaskEditForm, TaskCommentForm
from projector.filters import TaskFilter
from projector.views.project import ProjectView

from richtemplates.shortcuts import get_json_response
from richtemplates.forms import DynamicActionChoice, DynamicActionFormFactory

login_required_m = method_decorator(login_required)

class TaskListView(ProjectView):
    """
    Task for project listing view.
    """

    template_name='projector/project/task/list.html'
    perms_private = ['view_project', 'can_view_tasks']

    def response(self, request, username, project_slug):
        task_list = Task.objects.filter(project__id=self.project.id)\
                .select_related('priority', 'status', 'author', 'project')
        filters = TaskFilter(self.request.GET, queryset=task_list,
            project=self.project)
        if self.request.GET and 'id' in self.request.GET and \
                self.request.GET['id'] and filters.qs.count() == 1:
            task = filters.qs[0]
            messages.info(self.request, _("One task matched - redirecting..."))
            return redirect(task.get_absolute_url())
        self.context['filters'] = filters
        return self.context

class TaskDetailView(ProjectView):
    """
    Task details view.
    Users may update task here.
    """

    template_name = 'projector/project/task/detail.html'
    perms_private = ['view_project', 'can_view_tasks']

    def response(self, request, username, project_slug, task_id):
        task = get_object_or_404(
            Task.objects.select_related('type', 'priority', 'status', 'owner',
                'author', 'editor', 'milestone', 'component', 'project'),
            id = task_id,
            project__author__username = username,
            project__slug = project_slug)

        # We create formset for comment here as comment is only optional
        CommentFormset = formset_factory(TaskCommentForm, extra=1)

        destinations = task.status.destinations.all()
        # Init choices
        task_action_choices = [
            DynamicActionChoice(0, _("Don't change status")),
        ]
        if request.user.has_perm('can_change_task', task.project):
            if destinations:
                task_action_choices.append(DynamicActionChoice(1,
                    _("Change status"),
                    {'new_status': forms.ModelChoiceField(
                        queryset=destinations.exclude(id=task.status.id),
                        empty_label=None)
                    }))

        TaskActionForm = DynamicActionFormFactory(task_action_choices)
        action_form = TaskActionForm(request.POST or None, request.FILES or None)

        comment_formset = CommentFormset(request.POST or None)
        if request.method == 'POST':
            if not request.user.has_perm('can_change_task', task.project):
                raise PermissionDenied()

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
                task.editor_ip = request.META.get('REMOTE_ADDR', '')
                # action_type number as defined before at DynamicActionChoices
                action_type = data['action_type']
                if request.user.has_perm('can_change_task', task.project):
                    if action_type == 1:
                        task.status = data['new_status']
                if action_type > 0 or comment:
                    messages.success(request, _("Task updated successfully"))
                    task.save()
                    task.comment = comment
                    task.create_revision()
                    task.notify()
                else:
                    messages.warning(request, _("There were no changes"))
                return redirect(task.get_absolute_url())
            else:
                logging.error(action_form.errors)

        self.context['task'] = task
        self.context['is_watched'] = task.is_watched(request.user)
        self.context['now'] = datetime.datetime.now()
        self.context['action_form'] = action_form
        self.context['comment_formset'] = comment_formset

        return self.context

class TaskCreateView(ProjectView):
    """
    New Task creation view.
    """

    template_name = 'projector/project/task/create.html'
    perms_private = ['view_project', 'can_add_task']

    @login_required_m
    def response(self, request, username, project_slug):
        initial = {
            'owner': request.user.username, # form's owner is UserByNameField
        }
        instance = Task.objects.get_for_project(self.project)
        instance.author = request.user
        instance.author_ip = request.META.get('REMOTE_ADDR', '')
        instance.editor = instance.author
        instance.editor_ip = instance.author_ip

        form = TaskForm(request.POST or None, initial=initial, instance=instance)

        if request.method == 'POST':
            if form.is_valid():
                task = form.save(
                    editor = request.user,
                    editor_ip = request.META.get('REMOTE_ADDR', ''),
                )
                task.create_revision()
                messages.success(request, _("Task created succesfully."))
                task.notify()
                return redirect(task.get_absolute_url())

        self.context['form'] = form

        return self.context

class TaskEditView(ProjectView):
    """
    Edit Task meta information. task_details edits the rest.
    """

    template_name = 'projector/project/task/create.html'
    perms_private = ['view_project', 'can_change_task']

    def response(self, request, username, project_slug, task_id):
        task = get_object_or_404(Task, id=task_id,
            project__author__username=username, project__slug=project_slug)

        if request.method == 'POST':
            form = TaskEditForm(request.POST, instance=task)
            if form.is_valid():
                task = form.save(
                    editor=request.user,
                    editor_ip=request.META.get('REMOTE_ADDR', ''),
                )
                task.create_revision()
                messages.success(request, _("Task updated successfully."))
                task.notify()
                return redirect(task.get_absolute_url())
        else:
            form = TaskEditForm(instance=task, initial={
                'owner': task.owner and task.owner.username or None,
            })

        self.context['form'] = form

        return self.context

class TaskWatchView(ProjectView):
    """
    Makes request's user watching this task.
    """

    perms_private = ['view_project', 'can_view_tasks']

    def response(self, request, username, project_slug, task_id):
        task = get_object_or_404(Task, id=task_id,
            project__author__username=username, project__slug=project_slug)
        if request.method == 'POST':
            task.watch(request.user)
            if request.is_ajax():
                return get_json_response()
            return redirect(task.get_absolute_url())
        else:
            # Only POST methods are allowed here
            raise PermissionDenied()

class TaskUnwatchView(ProjectView):
    """
    Makes request's user watching this task.
    """

    perms_private = ['view_project', 'can_view_tasks']

    def response(self, request, username, project_slug, task_id):
        task = get_object_or_404(Task, id=task_id,
            project__author__username=username, project__slug=project_slug)
        if request.method == 'POST':
            if request.is_ajax():
                return get_json_response()
            task.unwatch(request.user)
            return redirect(task.get_absolute_url())
        else:
            # Only POST methods are allowed here
            raise PermissionDenied()

