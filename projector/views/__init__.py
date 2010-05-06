from django.views.generic import simple
from django.http import Http404

from livesettings.views import group_settings

def home(request, template_name='projector/home.html'):

    return simple.direct_to_template(request, {'template': template_name})

def settings(request):
    """
    Wrapper for standard livesettings view allowing only superusers to make
    projector-wide settings changes.
    If not requested by superuser 404 would be returned - not 403 as we don't
    want to expose this page to anyone at all.
    """
    if not (request.user.is_authenticated() and request.user.is_superuser):
        raise Http404
    return group_settings(request, 'PROJECTOR')

