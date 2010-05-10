from projector.models import Membership

def get_project_permissions(project=None, for_bit=None, user=None):
    """
    Usage::

       {% get_project_permissions PROJECT for USER [as "my_var"] %}

    Example::

       {% get_project_permissions project for request.user as "user_permissions" %}
    """
    assert project and for_bit == "for" and user
    try:
        return Membership.objects.get(project=project, member=user).all_perms
    except Membership.DoesNotExist:
        return []
get_project_permissions.function = True

