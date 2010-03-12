import authority

from authority import permissions
from projector.models import Project

class ProjectPermission(permissions.BasePermission):
    label = 'project_permission'
    #checks = ['add_member', 'delete_member']
    checks = [
        'view',
        'add_member_to',
        'delete_member_from',
        'view_tasks_for',
        'can_add_task_to',
        'can_change_task_to',
        'can_read_repository',
        'can_write_repository',
    ]
    

authority.register(Project, ProjectPermission)

