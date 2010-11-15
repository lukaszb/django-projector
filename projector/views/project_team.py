import logging

from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext as _
from django.contrib.admin.util import NestedObjects
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType

from projector.models import Team
from projector.views.project import ProjectView
from projector.forms import TeamForm, ProjectTeamPermissionsForm, TeamDeleteForm

from guardian.shortcuts import get_perms
from guardian.models import GroupObjectPermission

class TeamListView(ProjectView):
    """
    Returns teams view.
    """

    template_name = 'projector/project/teams/home.html'
    perms_private = ['view_project', 'view_teams_project']

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

    template_name = 'projector/project/teams/add.html'
    perms = ['view_project', 'add_team_project']

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

    template_name = 'projector/project/teams/edit.html'
    perms = ['view_project', 'change_team_project']

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

class TeamDeleteView(ProjectView):
    """
    Removes Group membership from the project.
    """

    template_name = 'projector/project/teams/delete.html'
    perms = ['view_project', 'can_delete_team']

    def response(self, request, username, project_slug, name):
        team = get_object_or_404(
            Team.objects.select_related('group', 'project'),
            project__author__username=username,
            project__slug=project_slug, group__name=name)

        group, project = team.group, team.project

        collector = NestedObjects()
        team._collect_sub_objects(collector)
        form = TeamDeleteForm(request.POST or None)
        perms_to_delete = GroupObjectPermission.objects.filter(
            group = group,
            content_type = ContentType.objects.get_for_model(project),
            object_pk = project.id)

        if request.method == 'POST':
            # Confirm removal
            if form.is_valid():
                msg = _("Team removed")
                messages.success(request, msg)
                team.delete()
                perms_to_delete.delete()
                return redirect(project.get_teams_url())
            else:
                msg = _("Couldn't remove team")
                messages.error(request, msg)

        context = {
            'project': project,
            'team': team,
            'form': form,
            'to_delete': collector.nested(),
            'team_perms': perms_to_delete,
        }
        return context

