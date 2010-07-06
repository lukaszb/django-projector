import logging

from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext as _
from django.contrib import messages

from projector.models import Team
from projector.views.project import ProjectView
from projector.forms import TeamForm, ProjectTeamPermissionsForm

from guardian.shortcuts import get_perms

class TeamListView(ProjectView):
    """
    Returns teams view.
    """

    perms = ProjectView.perms + ['view_teams_project']
    template_name = 'projector/project/teams/home.html'

    def response(self, request, username, project_slug):
        teams = Team.objects.filter(project=self.project)
        context = {
            'project': self.project,
            'team_list': teams,
        }
        return context

class TeamAddView(ProjectView):
    """
    Adds team for a project.
    """

    perms = ProjectView.perms + ['add_team_project']
    template_name = 'projector/project/teams/add.html'

    def response(self, request, username, project_slug):
        team = Team(
            project = self.project,
        )
        form = TeamForm(request.POST or None, instance=team)

        if request.method == 'POST' and form.is_valid():
            logging.info("Saving team %s for project '%s'"
                % (form.instance.group, form.instance.project))
            form.save()
            return redirect(self.project.get_teams_url())
        elif form.errors:
            logging.error("Form contains errors:\n%s" % form.errors)

        context = {
            'project': form.instance.project,
            'form': form,
        }
        return context

class TeamEditView(ProjectView):
    """
    Manages settings and permissions of project's team.
    """

    perms = ProjectView.perms + ['change_team_project']
    template_name = 'projector/project/teams/edit.html'

    def response(self, request, username, project_slug, name):
        team = get_object_or_404(
            Team.objects.select_related('group', 'project'),
            project__author__username=username,
            project__slug=project_slug, group__name=name)

        group, project = team.group, team.project
        team_perms = get_perms(group, project)

        form = ProjectTeamPermissionsForm(request.POST or None,
            team = team,
            initial_permissions = team_perms,
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
            'project': self.project,
            'form': form,
            'team': team,
            'team_perms': team_perms,
        }
        return context

