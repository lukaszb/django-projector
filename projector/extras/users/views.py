from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.template import RequestContext
from django.shortcuts import render_to_response

from projector.models import Team, Project
from projector.extras.users.forms import UserProfileForm

def user_list(request, template_name='projector/accounts/user_list.html'):
    user_list = User.objects.all()
    context = {
        'user_list': user_list,
    }
    return render_to_response(template_name, context, RequestContext(request))

def user_homepage(request,
        template_name='projector/accounts/user_homepage.html'):
    if not request.user.is_authenticated():
        msg = _("You are not logged in. You may view only public content "
            "of this website")
        messages.warning(request, msg)
        return render_to_response(template_name, {}, RequestContext(request))
    # Authed user homepage
    context = {
        'profile': request.user.get_profile(),
        'owned_task_list': request.user.owned_task\
            .select_related('status', 'project', 'priority',
                'milestone', 'component')\
            .filter(status__is_resolved=False)\
            .order_by('project')
    }
    return render_to_response(template_name, context, RequestContext(request))

def profile_detail(request, username,
        template_name='projector/accounts/profile.html'):
    """
    Public profile of the given user.
    """
    user = get_object_or_404(User, username=username)
    context = {
        'profile': user.get_profile(),
        'project_list': Project.objects.for_user(request.user),
        'teams': Team.objects.for_user(user)
    }
    return render_to_response(template_name, context, RequestContext(request))

@login_required
def profile_edit(request, username,
        template_name='projector/accounts/profile_edit.html'):
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
    return render_to_response(template_name, context, RequestContext(request))

