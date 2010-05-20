from projector.models import Membership, Watchable

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

def put_username_into_url(value, user):
    """
    Puts username into url for the given User object.
    """
    if not user.is_authenticated():
        return value
    prefixes = ['http://', 'https://', 'ftp://']
    for prefix in prefixes:
        if value.lower().startswith(prefix):
            value = ''.join((
                value[:len(prefix)], user.username, '@', value[len(prefix):]))
    return value
put_username_into_url.filter = True

def is_watched(watchable, by_bit=None, user=None):
    """
    Usage::

       {% is_watched WATCHABLE by USER [as "my_var"] %}

    Provided context contains ``task`` and ``user`` objects we can use it as
    follows::

       {% is_watched task by user %}
    """
    assert watchable and isinstance(watchable, Watchable)
    assert by_bit == 'by'
    assert user
    return watchable.is_watched(user)
is_watched.function = True

