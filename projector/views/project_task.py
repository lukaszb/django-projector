import datetime

from django.shortcuts import get_object_or_404, redirect
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator
from django.utils.simplejson import dumps

from projector.models import Task
from projector.forms import TaskForm, TaskEditForm
from projector.filters import TaskFilter
from projector.views.project import ProjectView

from richtemplates.shortcuts import get_json_response

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


class TaskListDataView(ProjectView):
    """
    Tasks data for charts.
    """

    def response(self, request, username, project_slug):
        import random
        import pyofc2
        t = pyofc2.title(text=_("Tasks"))
        b1 = pyofc2.bar()
        b1.values = range(10)
        b2 = pyofc2.bar()
        b2.values = [random.randint(0,9) for i in range(9)]
        b2.colour = '#56acde'
        chart = pyofc2.open_flash_chart()
        chart.title = t
        chart.add_element(b1)
        chart.add_element(b2)
        return HttpResponse(chart.render())


class TaskDetailView(ProjectView):
    """
    Task detail view.
    Users may update task here.
    """

    template_name = 'projector/project/task/detail.html'
    perms_private = ['view_project', 'can_view_tasks']
    perms_POST = ['can_change_task']

    def response(self, request, username, project_slug, task_id):
        task = get_object_or_404(
            Task.objects.select_related('type', 'priority', 'status', 'owner',
                'author', 'editor', 'milestone', 'component', 'project'),
            id = task_id,
            project__author__username = username,
            project__slug = project_slug)

        self.context['task'] = task
        self.context['is_watched'] = task.is_watched(request.user)
        self.context['now'] = datetime.datetime.now()

        return self.context

class TaskCreateView(ProjectView):
    """
    New Task creation view.
    """

    template_name = 'projector/project/task/create.html'
    perms = ProjectView.perms + ['can_add_task']

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
    Edit Task meta information. task_detail edits the rest.
    """

    template_name = 'projector/project/task/create.html'
    perms = ['can_change_task']

    @login_required_m
    def response(self, request, username, project_slug, task_id):
        task = get_object_or_404(Task, id=task_id,
            project__author__username=username, project__slug=project_slug)

        if request.method == 'POST':
            form = TaskEditForm(request.POST, instance=task)
            if form.is_valid():
                if request.user.is_authenticated():
                    editor = request.user
                else:
                    editor = User.get_anonymous() # available from guardian
                task = form.save(
                    editor=editor,
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

