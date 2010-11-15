import logging

from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext as _
from django.contrib import messages
from django.contrib.admin.util import NestedObjects
from django.contrib.contenttypes.models import ContentType

from projector.models import Membership
from projector.views.project import ProjectView
from projector.forms import MembershipForm, ProjectMembershipPermissionsForm
from projector.forms import MembershipDeleteForm

from guardian.models import UserObjectPermission
from guardian.shortcuts import get_perms

class MemberListView(ProjectView):
    """
    Returns members view.
    """

    template_name = 'projector/project/members/home.html'

    def response(self, request, username, project_slug):
        memberships = Membership.objects.filter(project=self.project)
        context = {
            'project': self.project,
            'memberships': memberships,
        }
        return context

class MemberAddView(ProjectView):
    """
    Adds member for a project.
    """

    template_name = 'projector/project/members/add.html'
    perms = ['view_project', 'add_member_project']

    def response(self, request, username, project_slug):
        membership = Membership(
            project = self.project,
        )
        form = MembershipForm(request.POST or None, instance=membership)

        if request.method == 'POST' and form.is_valid():
            logging.info("Saving member %s for project '%s'"
                % (form.instance.member, form.instance.project))
            form.save()
            return redirect(self.project.get_members_url())
        elif form.errors:
            logging.error("Form contains errors:\n%s" % form.errors)

        context = {
            'project': form.instance.project,
            'form': form,
        }
        return context

class MemberEditView(ProjectView):
    """
    Manages membership settings and permissions of project's member.
    """

    template_name = 'projector/project/members/edit.html'
    perms = ['view_project', 'can_change_member']

    def response(self, request, username, project_slug, member_username):
        membership = get_object_or_404(
            Membership.objects.select_related('project', 'member'),
            project__slug=project_slug,
            project__author__username=username,
            member__username=member_username)\

        member = membership.member
        project = membership.project
        if project.author == member:
            messages.warning(request, _("Project owner's membership cannot be "
                "modified. He/She has all permissions for this project."))
            return redirect(project.get_members_url())
        member_perms = get_perms(member, project)

        form = ProjectMembershipPermissionsForm(request.POST or None,
            membership = membership,
            initial_permissions = member_perms,
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
            'project': self.project,
            'form': form,
            'membership': membership,
            'member_perms': member_perms,
        }
        return context

class MemberDeleteView(ProjectView):
    """
    Removes member from project.
    """

    template_name = 'projector/project/members/delete.html'
    perms = ['view_project', 'delete_member_project']

    def response(self, request, username, project_slug, member_username):
        membership = get_object_or_404(
            Membership.objects.select_related('project', 'member'),
            project__slug=project_slug,
            project__author__username=username,
            member__username=member_username)\

        member = membership.member
        project = membership.project

        if project.author == member:
            messages.warning(request, _("Project owner's membership cannot be "
                "removed."))
            return redirect(project.get_members_url())
        collector = NestedObjects()
        membership._collect_sub_objects(collector)
        form = MembershipDeleteForm(request.POST or None)
        perms_to_delete = UserObjectPermission.objects.filter(
            user = member,
            content_type = ContentType.objects.get_for_model(project),
            object_pk = project.id)

        if request.method == 'POST':
            # Confirm removal
            if form.is_valid() and project.author != member:
                msg = _("Membership removed")
                messages.success(request, msg)
                membership.delete()
                perms_to_delete.delete()
                return redirect(project.get_members_url())
            else:
                msg = _("Couldn't remove membership")
                messages.error(request, msg)
                if project.author == member:
                    msg = _("Project's author cannot be removed")
                    messages.error(request, msg)
        context = {
            'project': project,
            'membership': membership,
            'form': form,
            'to_delete': collector.nested(),
            'member_perms': perms_to_delete,
        }
        return context

