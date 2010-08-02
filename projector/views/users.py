from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.shortcuts import get_object_or_404, redirect
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse

from projector.core.controllers import View
from projector.forms import UserProfileForm, UserConvertToTeamForm
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

class UserDashboardView(View):
    """
    Edit profile view.
    """

    template_name = 'projector/accounts/dashboard.html'

    def response(self, request):
        if request.user.is_anonymous() or not request.user.is_active:
            raise PermissionDenied
        form = UserProfileForm(request.POST or None,
            instance=request.user.get_profile())
        if request.method == 'POST' and form.is_valid():
            form.save()
            message = _("Profile updated successfully")
            messages.success(request, message)
            return redirect(reverse('projector_users_profile_detail',
                kwargs={'username': request.user.username}))
        self.context['form'] = form
        self.context['profile'] = form.instance
        return self.context

class UserDashboardConvert2TeamView(View):
    """
    Convert to team view.
    """

    template_name = 'projector/accounts/dashboard-convert-confirm.html'

    def response(self, request):
        if request.user.is_anonymous() or not request.user.is_active:
            raise PermissionDenied
        if request.user.get_profile().is_team:
            messages.warning(request,
                "This account is already converted to team!")
            return redirect(reverse('projector_users_profile_detail',
                kwargs={'username': request.user.username}))
        form = UserConvertToTeamForm(request.POST or None)
        form.user = request.user
        if request.method == 'POST':
            if form.is_valid():
                msg = _("You have successfully converted account into Team")
                messages.success(request, msg)
                return redirect(reverse('projector_users_profile_detail',
                    kwargs={'username': request.user.username}))
            else:
                msg = _("Errors occured during account to team conversion")
                messages.error(request, msg)
        self.context['form'] = form
        self.context['profile'] = request.user.get_profile()
        return self.context

