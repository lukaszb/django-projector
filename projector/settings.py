import os
import logging

from django.conf import settings

abspath = lambda *p: os.path.abspath(os.path.join(*p))

ALWAYS_SEND_MAILS_TO_MEMBERS = getattr(settings,
    'PROJECTOR_ALWAYS_SEND_MAILS_TO_MEMBERS', False)

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

BASIC_AUTH_REALM = getattr(settings,
    'PROJECTOR_BASIC_AUTH_REALM', 'Projector Basic Auth')

CHANGESETS_PAGINATE_BY = getattr(settings,
    'PROJECTOR_CHANGESETS_PAGINATE_BY', 10)

CREATE_PROJECT_ASYNCHRONOUSLY = getattr(settings,
    'PROJECTOR_CREATE_PROJECT_ASYNCHRONOUSLY', True)

EDITABLE_PERMISSIONS = getattr(settings,
    'PROJECTOR_EDITABLE_PERMISSIONS',
    (
        'change_project',
        'admin_project',
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
)

FROM_EMAIL_ADDRESS = settings.DEFAULT_FROM_EMAIL

MAX_PROJECTS_PER_USER = getattr(settings,
    'PROJECTOR_MAX_PROJECTS_PER_USER', 50)

MILESTONE_DEADLINE_DELTA = getattr(settings,
    'PROJECTOR_MILESTONE_DEADLINE_DELTA', 60)

MILIS_BETWEEN_PROJECT_CREATION = getattr(settings,
    'PROJECTOR_MILIS_BETWEEN_PROJECT_CREATION', 15*1000)

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

PRIVATE_ONLY = getattr(settings,
    'PROJECTOR_PRIVATE_ONLY', False)

SEND_MAIL_ASYNCHRONOUSELY = getattr(settings,
    'PROJECTOR_SEND_MAIL_ASYNCHRONOUSELY', True)

SEND_MAILS_USING_MAILER = False

TASK_EMAIL_SUBJECT_SUMMARY_FORMAT = getattr(settings,
    'PROJECTOR_TASK_EMAIL_SUBJECT_SUMMARY_FORMAT',
    "[$project] #$id: $summary")

PROJECTOR = {
    'ALWAYS_SEND_MAILS_TO_MEMBERS': 'ALWAYS_SEND_MAILS_TO_MEMBERS',
    'BANNED_PROJECT_NAMES': BANNED_PROJECT_NAMES,
    'BASIC_AUTH_REALM': BASIC_AUTH_REALM,
    'CHANGESETS_PAGINATE_BY': CHANGESETS_PAGINATE_BY,
    'CREATE_PROJECT_ASYNCHRONOUSLY': CREATE_PROJECT_ASYNCHRONOUSLY,
    'EDITABLE_PERMISSIONS': EDITABLE_PERMISSIONS,
    'FROM_EMAIL_ADDRESS': settings.DEFAULT_FROM_EMAIL,
    'MAX_PROJECTS_PER_USER': MAX_PROJECTS_PER_USER,
    'MILESTONE_DEADLINE_DELTA': MILESTONE_DEADLINE_DELTA,
    'MILIS_BETWEEN_PROJECT_CREATION': MILIS_BETWEEN_PROJECT_CREATION,
    'PRIVATE_ONLY': PRIVATE_ONLY,
    'PROJECTS_ROOT_DIR': PROJECTS_ROOT_DIR,
    'SEND_MAILS_USING_MAILER': SEND_MAILS_USING_MAILER,
    'TASK_EMAIL_SUBJECT_SUMMARY_FORMAT': TASK_EMAIL_SUBJECT_SUMMARY_FORMAT,
}

def get_config_value(key):
    if key.startswith('PROJECTOR_'):
        key = key[key.find('PROJECTOR_'):]
    return globals()[key]
    #return PROJECTOR[key]

