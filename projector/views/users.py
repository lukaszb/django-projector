from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.shortcuts import get_object_or_404, redirect
from django.core.exceptions import PermissionDenied

from projector.core.controllers import View
from projector.forms import UserProfileForm
from projector.models import Team, Project

class UserListView(View):
    template_name = 'projector/accounts/user_list.html'

    def response(self, request):
        user_list = User.objects.all()
        context = {
            'user_list': user_list,
        }
        return context

class UserHomepageView(View):
    template_name = 'projector/accounts/user_homepage.html'

    def response(self, request):
        if not request.user.is_authenticated():
            msg = _("You are not logged in. You may view only public content "
                "of this website")
            messages.warning(request, msg)
            return {}
        # Authed user homepage
        context = {
            'profile': request.user.get_profile(),
            'owned_task_list': request.user.owned_task\
                .select_related('status', 'project', 'priority',
                    'milestone', 'component')\
                .filter(status__is_resolved=False)\
                .order_by('project')
        }
        return context

class UserProfileDetailView(View):
    """
    Public profile of the given user.
    """
    template_name = 'projector/accounts/profile.html'

    def response(self, request, username):
        user = get_object_or_404(User, username=username)
        context = {
            'profile': user.get_profile(),
            'project_list': Project.objects.for_user(request.user),
            'teams': Team.objects.for_user(user)
        }
        return context

class UserProfileEditView(View):
    """
    Edit profile view.
    """
    template_name = 'projector/accounts/profile_edit.html'

    def response(self, request, username):
        user = get_object_or_404(User, username=username)
        if request.user != user:
            raise PermissionDenied
        form = UserProfileForm(request.POST or None,
            instance=user.get_profile())
        if request.method == 'POST' and form.is_valid():
            form.save()
            message = _("Profile updated successfully")
            messages.success(request, message)
            return redirect(user.get_absolute_url())
        context = {
            'form': form,
        }
        return context

