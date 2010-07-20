from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext as _
from django.contrib import messages

from projector.models import Component
from projector.views.project import ProjectView
from projector.forms import ComponentForm

class ComponentListView(ProjectView):
    """
    Returns components view.
    """

    template_name = 'projector/project/components/home.html'

    def response(self, request, username, project_slug):
        component_list = self.project.component_set\
            .annotate(Count('task'))
        context = {
            'project': self.project,
            'component_list': component_list,
        }

        return context

class ComponentDetailView(ProjectView):
    """
    Returns component detail view.
    """

    template_name = 'projector/project/components/detail.html'

    def response(self, request, username, project_slug, component_slug):
        component = get_object_or_404(Component, project=self.project,
            slug=component_slug)
        context = {
            'project': self.project,
            'component': component,
        }
        return context

class ComponentCreateView(ProjectView):
    """
    Adds component for project.
    """

    template_name = 'projector/project/components/add.html'
    perms = ['change_project']

    def response(self, request, username, project_slug):
        component = Component(project=self.project)
        form = ComponentForm(request.POST or None, instance=component)
        if request.method == 'POST' and form.is_valid():
            component = form.save()
            msg = _("Component added successfully")
            messages.success(request, msg)
            return redirect(component.get_absolute_url())
        context = {
            'project': self.project,
            'form': form,
        }
        return context

class ComponentEditView(ProjectView):
    """
    Edits chosen component.
    """

    template_name = 'projector/project/components/edit.html'
    perms = ['change_project']

    def response(self, request, username, project_slug, component_slug):
        component = get_object_or_404(Component,
            project=self.project, slug=component_slug)
        form = ComponentForm(request.POST or None, instance=component)
        if request.method == 'POST' and form.is_valid():
            component = form.save()
            msg = _("Component updated successfully")
            messages.success(request, msg)
            return redirect(component.get_absolute_url())
        context = {
            'project': self.project,
            'form': form,
        }
        return context

