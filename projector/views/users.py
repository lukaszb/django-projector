from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.sites.models import Site
from django.utils.translation import ugettext as _
from django.shortcuts import get_object_or_404, redirect
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse

from projector.core.controllers import View
from projector.forms import UserProfileForm, UserConvertToTeamForm
from projector.forms import ExternalForkWizard, ExternalForkSourcesForm
from projector.models import Team, Project
from projector.settings import get_config_value


def can_fork_external():
    """
    External fork is available if ``FORK_EXTERNAL_MAP`` is set to ``True``
    **AND** ``FORK_EXTERNAL_MAP`` is not empty dict.
    """
    if get_config_value('FORK_EXTERNAL_ENABLED') is True and \
        get_config_value('FORK_EXTERNAL_MAP'):
        return True
    return False


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
        self.context['site'] = Site.objects.get_current()
        self.context['can_fork_external'] = can_fork_external()
        return self.context


class UserDashboardForkView(View):
    """
    Fork external project view.
    """

    template_name = 'projector/accounts/dashboard_fork.html'
    login_required = True

    def response(self, request):
        if get_config_value('FORK_EXTERNAL_ENABLED') is not True:
            messages.warning(request, _("External forks are disabled"))
            return redirect(reverse('projector_dashboard'))
        elif not get_config_value('FORK_EXTERNAL_MAP'):
            messages.warning(request, _("No external fork forms available"))
            return redirect(reverse('projector_dashboard'))

        # Zero at forms list parameter of wizard is only a placeholder - we
        # change form_list dynamically at wizard's ``process_step`` method
        wizard = ExternalForkWizard([ExternalForkSourcesForm, 0])
        wizard.extra_context['profile'] = request.user.get_profile()
        return wizard(request)


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

