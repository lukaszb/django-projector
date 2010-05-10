import authority

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Group
from authority import permissions
from authority.models import Permission
from projector.models import Project
from projector.exceptions import NotApplicableError

class ProjectPermission(permissions.BasePermission):
    label = 'project_permission'
    #checks = ['add_member', 'delete_member']
    checks = [
        'view',

        'view_members', # View all members for the project (so plural)
        'add_member',
        'change_member',
        'delete_member',

        'view_teams', # View all teams for the project (so plural)
        'add_team',
        'change_team',
        'delete_team',

        'view_tasks', # View all tasks for the project (so plural)
        'add_task',
        'change_task',

        'read_repository',
        'write_repository',
    ]

    @staticmethod
    def get_local_checks():
        """
        Returns list of *local checks* (not from django's own
        authorization framework).
        """
        local_checks = [check for check in ProjectPermission.checks
            if check.endswith('_project')]
        return local_checks

authority.register(Project, ProjectPermission)

def get_or_create_permisson(codename, obj, user=None, group=None,
        creator=None, approved=True):
    """
    Returns permission object for given codename, obj and user/group.
    If user/group does not have this permission, it is created.
    If creator is not given, it is assumed that given user is the creator.
    You may pass only one of user or group, not both.
    """
    if user and group:
        raise NotApplicableError("Cannot get/create permission for both user "
            "and group at once")
    if creator is None:
        creator = user
    perm_obj, created = Permission.objects.get_or_create(
        creator = creator,
        content_type = ContentType.objects.get_for_model(obj),
        object_id = obj.pk,
        codename = codename,
        user = user,
        group = group,
        approved = approved
    )
    return perm_obj

def remove_permission(codename, obj, user=None, group=None):
    """
    Deletes chosen permission from database.
    """
    qs = Permission.objects.filter(
        content_type = ContentType.objects.get_for_model(obj),
        object_id = obj.pk,
        codename = codename,
    )
    if user:
        qs = qs.filter(user=user)
    if group:
        qs = qs.filter(group)
    import logging
    logging.error("Removes: %s" % qs)
    qs.delete()

def get_perms_for_user(user, obj, content_type=None):
    """
    Returns list of permissions for the given user/object.
    """
    if content_type is None:
        content_type = ContentType.objects.get_for_model(obj)
    perms = Permission.objects.filter(
        user = user,
        content_type = content_type,
        object_id = obj.id,
    )
    return perms

def get_perms_for_group(group, obj, content_type=None):
    """
    Returns list of permissions for the given group/object.
    """
    if content_type is None:
        content_type = ContentType.object.get_for_model(obj)
    perms = Permission.objects.filter(
        group = group,
        content_type = content_type,
        object_id = obj.id,
    )
    return perms

def get_perms(user_or_group, obj):
    """
    Returns list of permissions for the given user or group and object.
    """
    content_type = ContentType.objects.get_for_model(obj)
    if isinstance(user_or_group, User):
        return get_perms_for_user(user_or_group, obj,
            content_type = content_type)
    elif isinstance(user_or_group, Group):
        return get_perms_for_group(user_or_group, obj,
            content_type = content_type)
    raise NotApplicableError("Can retrieve permissions only for user or group")

