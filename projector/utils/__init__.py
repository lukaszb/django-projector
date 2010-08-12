"""
Utilities and helpers for ``django-projector``.
"""
import os

from django.conf import settings
from projector.utils.basic import str2obj, codename_to_label

__all__ = [
    'abspath',
    'codename_to_label',
    'str2obj',
    'using_projector_profile',
]

abspath = lambda *paths: os.path.abspath(os.path.join(*paths))

def using_projector_profile():
    """
    Returns True if ``AUTH_PROFILE_MODULE`` is set to ``projector.UserProfile``
    and False otherwise.
    """
    auth_profile_module = getattr(settings, 'AUTH_PROFILE_MODULE', False)
    return auth_profile_module == 'projector.UserProfile'

