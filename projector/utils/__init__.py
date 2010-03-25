import os

from django.conf import settings

abspath = lambda *paths: os.path.abspath(os.path.join(*paths))

def using_projector_profile():
    """
    Returns True if ``AUTH_PROFILE_MODULE`` is set to ``projector.UserProfile``
    and False otherwise.
    """
    auth_profile_module = getattr(settings, 'AUTH_PROFILE_MODULE', False)
    return auth_profile_module == 'projector.UserProfile'

