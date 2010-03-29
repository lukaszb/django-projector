from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.contrib import messages
from django.core.exceptions import PermissionDenied

from annoying.decorators import render_to
from projector.models import Project, Task
from projector.extras.users.forms import UserProfileForm
from richtemplates.utils import get_user_profile_model

@login_required
@render_to('projector/accounts/user_list.html')
def user_list(request):
    user_list = User.objects.all()
    context = {
        'user_list': user_list,
    }
    return context

@render_to('projector/accounts/user_homepage.html')
def user_homepage(request):
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

@login_required
@render_to('projector/accounts/profile.html')
def profile_detail(request, username):
    user = get_object_or_404(User, username=username)
    context = {
        'profile': user.get_profile(),
    }
    return context

@login_required
@render_to('richtemplates/accounts/profile_edit.html')
def profile_edit(request, username):
    """
    Edit profile view.
    """
    user = get_object_or_404(User, username=username)
    if request.user != user:
        raise PermissionDenied
    form = UserProfileForm(request.POST or None, instance=user.get_profile())
    if request.method == 'POST' and form.is_valid():
        form.save()
        message = _("Profile updated successfully")
        messages.success(request, message)
        return redirect(user.get_absolute_url())
    context = {
        'form': form,
    }
    return context

