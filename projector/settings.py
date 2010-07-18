import os
import logging

from django.conf import settings

abspath = lambda *p: os.path.abspath(os.path.join(*p))

BANNED_PROJECT_NAMES = getattr(settings, 'PROJECTOR_BANNED_PROJECT_NAMES', ())
BANNED_PROJECT_NAMES += (
    'account', 'accounts',
    'add',
    'admin', 'admins',
    'api',
    'author', 'authors',
    'ban',
    'category', 'categories',
    'change',
    'create',
    'default',
    'delete',
    'edit', 'edits',
    'etc',
    'issue', 'issues',
    'mail', 'mails',
    'message', 'messages',
    'manager', 'managers',
    'private',
    'profile', 'profiles',
    'projects',
    'register', 'registration',
    'remove',
    'task', 'tasks',
    'update',
    'user', 'users',
    'view',
)

CREATE_PROJECT_ASYNCHRONOUSLY = getattr(settings,
    'PROJECTOR_CREATE_PROJECT_ASYNCHRONOUSLY', True)

SEND_MAIL_ASYNCHRONOUSELY = getattr(settings,
    'PROJECTOR_SEND_MAIL_ASYNCHRONOUSELY', True)

MILIS_BETWEEN_PROJECT_CREATION = getattr(settings,
    'PROJECTOR_MILIS_BETWEEN_PROJECT_CREATION', 15*1000)

MAX_PROJECTS_PER_USER = getattr(settings,
    'PROJECTOR_MAX_PROJECTS_PER_USER', 50)

PROJECTS_ROOT_DIR = getattr(settings, 'PROJECTOR_PROJECTS_ROOT_DIR', None)
if PROJECTS_ROOT_DIR is None:
    logging.debug("django-projector: PROJECTOR_PROJECTS_ROOT_DIR not set "
        "- will not create repositories")
else:
    PROJECTS_ROOT_DIR = abspath(PROJECTS_ROOT_DIR)
    if not os.path.exists(PROJECTS_ROOT_DIR):
        os.mkdir(PROJECTS_ROOT_DIR)
        logging.info("django-projector: created %s directory"
            % PROJECTS_ROOT_DIR)

editable_perm_codenames = (
    'change_project',
    'change_config_project',
    'view_project',
    'can_read_repository',
    'can_write_to_repository',
    'can_change_description',
    'can_change_category',
    'can_add_task',
    'can_change_task',
    'can_delete_task',
    'can_view_tasks',
    'can_add_member',
    'can_change_member',
    'can_delete_member',
    'can_add_team',
    'can_change_team',
    'can_delete_team',
)

TASK_EMAIL_SUBJECT_SUMMARY_FORMAT = getattr(settings,
    'PROJECTOR_TASK_EMAIL_SUBJECT_SUMMARY_FORMAT',
    "[$project] #$id: $summary")

MILESTONE_DEADLINE_DELTA = getattr(settings,
    'PROJECTOR_MILESTONE_DEADLINE_DELTA', 60)

CHANGESETS_PAGINATE_BY = getattr(settings,
    'PROJECTOR_CHANGESETS_PAGINATE_BY', 10)

ALWAYS_SEND_MAILS_TO_MEMBERS = getattr(settings,
    'PROJECTOR_ALWAYS_SEND_MAILS_TO_MEMBERS', False)

BASIC_AUTH_REALM = getattr(settings,
    'PROJECTOR_BASIC_AUTH_REALM', 'Projector Basic Auth')

PRIVATE_ONLY = getattr(settings,
    'PROJECTOR_PRIVATE_ONLY', False)

PROJECTOR = {
    'BASIC_AUTH_REALM': BASIC_AUTH_REALM,
    'MILESTONE_DEADLINE_DELTA': MILESTONE_DEADLINE_DELTA,
    'CHANGESETS_PAGINATE_BY': CHANGESETS_PAGINATE_BY,
    'PROJECT_EDITABLE_PERMISSIONS': editable_perm_codenames,
    'SEND_MAILS_USING_MAILER': False,
    'FROM_EMAIL_ADDRESS': settings.DEFAULT_FROM_EMAIL,
    'ALWAYS_SEND_MAILS_TO_MEMBERS': ALWAYS_SEND_MAILS_TO_MEMBERS,
    'ALWAYS_ALLOW_READ_PUBLIC_PROJECTS': getattr(settings,
        'PROJECTOR_ALWAYS_ALLOW_READ_PUBLIC_PROJECTS', False),
    'TASK_EMAIL_SUBJECT_SUMMARY_FORMAT': TASK_EMAIL_SUBJECT_SUMMARY_FORMAT,
    'MILIS_BETWEEN_PROJECT_CREATION': MILIS_BETWEEN_PROJECT_CREATION,
    'MAX_PROJECTS_PER_USER': MAX_PROJECTS_PER_USER,
    'PRIVATE_ONLY': PRIVATE_ONLY,
}

def get_config_value(key):
    return PROJECTOR[key]

