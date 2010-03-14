import logging
import authority

from django.contrib.contenttypes.models import ContentType
from authority import permissions
from authority.models import Permission
from projector.models import Project

class ProjectPermission(permissions.BasePermission):
    label = 'project_permission'
    #checks = ['add_member', 'delete_member']
    checks = [
        'view',

        'add_member',
        'change_member',
        'delete_member',

        'view_tasks_for',
        'add_task_to',
        'change_task_to',

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

def get_or_create_permisson(user, project, codename, creator=None):
    """
    Returns permission object for given user/project/codename.
    If user does not have this permission, it is created.
    If creator is not given, it is assumed that given user
    is the creator.
    """
    if creator is None:
        creator = user
    if not '.' in codename:
        codename = '.'.join((ProjectPermission.label, codename))
    if not codename.endswith('_project'):
        codename += '_project'
    perm_obj, created = Permission.objects.get_or_create(
        creator = creator,
        content_type = ContentType.objects.get_for_model(project),
        object_id = project.id,
        codename = codename,
        user = user,
        approved = True,
    )
    return perm_obj

