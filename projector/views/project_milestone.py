from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext as _
from django.contrib import messages

from projector.models import Milestone
from projector.views.project import ProjectView
from projector.forms import MilestoneForm

class MilestoneListView(ProjectView):

    template_name = 'projector/project/milestones/home.html'

    def response(self, request, username, project_slug):
        milestone_list = self.project.milestone_set\
            .annotate(Count('task'))\
            .order_by('-created_at')
        self.context['milestone_list'] = milestone_list
        return self.context


class MilestoneGanttView(MilestoneListView):

    template_name = 'projector/project/milestones/gantt.html'

    def response(self, request, username, project_slug):
        milestone_list = self.project.milestone_set\
            .annotate(Count('task'))\
            .order_by('created_at')
        self.context['milestone_list'] = milestone_list
        self.context['milestone_first'] = milestone_list and milestone_list[0]
        if milestone_list:
            # Get last by deadline
            last = milestone_list[0]
            for milestone in milestone_list[1:]:
                if milestone.deadline > last.deadline:
                    last = milestone
            self.context['milestone_last'] = last
        return self.context


class MilestoneDetailView(ProjectView):
    """
    Returns milestone detail view.
    """

    template_name = 'projector/project/milestones/detail.html'

    def response(self, request, username, project_slug, milestone_slug):
        milestone = get_object_or_404(Milestone,
            project=self.project, slug=milestone_slug)
        context = {
            'project': self.project,
            'milestone': milestone,
        }
        return context

class MilestoneCreateView(ProjectView):
    """
    Adds milestone for project.
    """

    template_name = 'projector/project/milestones/add.html'
    perms = ['view_project', 'change_project']

    def response(self, request, username, project_slug):
        milestone = Milestone(project=self.project, author=request.user)
        form = MilestoneForm(request.POST or None, instance=milestone)
        if request.method == 'POST' and form.is_valid():
            milestone = form.save()
            msg = _("Milestone added successfully")
            messages.success(request, msg)
            return redirect(milestone.get_absolute_url())
        context = {
            'project': self.project,
            'form': form,
        }
        return context

class MilestoneEditView(ProjectView):
    """
    Edits chosen milestone.
    """

    template_name = 'projector/project/milestones/edit.html'
    perms = ['view_project', 'change_project']

    def response(self, request, username, project_slug, milestone_slug):
        milestone = get_object_or_404(Milestone, slug=milestone_slug)
        form = MilestoneForm(request.POST or None, instance=milestone)
        if request.method == 'POST' and form.is_valid():
            milestone = form.save()
            msg = _("Milestone updated successfully")
            messages.success(request, msg)
            return redirect(milestone.get_absolute_url())
        context = {
            'project': self.project,
            'form': form,
        }
        return context

