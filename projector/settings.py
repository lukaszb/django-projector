import os
import logging

from django.conf import settings

from projector.utils.basic import codename_to_label

abspath = lambda *p: os.path.abspath(os.path.join(*p))

BANNED_PROJECT_NAMES = getattr(settings, 'PROJECTOR_BANNED_PROJECT_NAMES', ())
BANNED_PROJECT_NAMES += (
    'account', 'accounts',
    'add',
    'admin',
    'api',
    'author', 'authors',
    'category', 'categories',
    'create',
    'edit', 'edits',
    'issue', 'issues',
    'mail', 'mails',
    'message', 'messages',
    'manager', 'managers',
    'profile', 'profiles',
    'projects',
    'register', 'registration',
    'task', 'tasks',
    'update',
    'user', 'users',
)

CREATE_PROJECT_ASYNCHRONOUSLY = getattr(settings,
    'PROJECTOR_CREATE_PROJECT_ASYNCHRONOUSLY', True)

SEND_MAIL_ASYNCHRONOUSELY = getattr(settings,
    'PROJECTOR_SEND_MAIL_ASYNCHRONOUSELY', True)

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
    'project_permission.view_project',

    'project_permission.view_members_project',
    'project_permission.add_member_project',
    'project_permission.change_member_project',
    'project_permission.delete_member_project',

    'project_permission.view_teams_project',
    'project_permission.add_team_project',
    'project_permission.change_team_project',
    'project_permission.delete_team_project',

    'project_permission.view_tasks_project',
    'project_permission.add_task_project',
    'project_permission.change_task_project',
    'project_permission.delete_task_project',

    'project_permission.read_repository_project',
    'project_permission.write_repository_project',
)

# Following settings may be changed dynamically (livesettings)

'''
PROJECTOR = ConfigurationGroup('PROJECTOR', _("Projector application settings"))

config_register(StringValue(
    PROJECTOR,
    'BASIC_AUTH_REALM',
    description = _("Basic auth realm text"),
    help_text = _("Text send when user is asked for credentials if he/she "
        "tries to work with project's repository."),
    default = 'Projector Basic Auth')
)

config_register(IntegerValue(
    PROJECTOR,
    'MILESTONE_DEADLINE_DELTA',
    description = _("Default days number for milestones"),
    help_text = _("Every milestone has its deadline and this number specifies "
                  "how many days would be given by default. It may be set to "
                  "any date during milestone creation process though."),
    default = 60)
)

config_register(BooleanValue(
    PROJECTOR,
    'ALWAYS_ALLOW_READ_PUBLIC_PROJECTS',
    description = _("Allow read public projects"),
    help_text = _("By default, authorization is required even if project is "
                  "public. However, if this is set to True, any user would "
                  "be allowed to read public projects' repositories."),
    default = False)
)


CHANGESETS_PAGINATE_BY_MIN = 1
CHANGESETS_PAGINATE_BY_MAX = 20

config_register(IntegerValue(
    PROJECTOR,
    'CHANGESETS_PAGINATE_BY',
    description = _("Changsets per page"),
    help_text = _("How many changesets are shown on one page at changeset "
                  "listing."),
    default = 10,
    validators = [IntegerValidator(
        CHANGESETS_PAGINATE_BY_MIN,
        CHANGESETS_PAGINATE_BY_MAX)
    ],
    )
)

config_register(RichMultipleStringValue(
    PROJECTOR,
    'PROJECT_EDITABLE_PERMISSIONS',
    description = _("Editable permissions per project"),
    help_text = _("Those permissions would be editable at project's 'members' "
                  "and teams' page."),
    default = editable_perm_codenames,
    choices = [(codename, codename_to_label(codename))
        for codename in editable_perm_codenames
    ],
))

config_register(BooleanValue(
    PROJECTOR,
    'SEND_MAILS_USING_MAILER',
    description = _("Send mails using django-mailer app"),
    help_text = _("django-mailer (http://github.com/jtauber/django-mailer) "
                  "would first store mails at database; it is necessary to "
                  "call 'send_mail' and 'retry_deferred' regularly (cron) "),
    default = False,
))

config_register(StringValue(
    PROJECTOR,
    'FROM_EMAIL_ADDRESS',
    description = _("Email address from which mails are send to the users"),
    default = settings.DEFAULT_FROM_EMAIL,
))

config_register(BooleanValue(
    PROJECTOR,
    'ALWAYS_SEND_MAILS_TO_MEMBERS',
    description = _("Always send mails to project's members"),
    help_text = _("If this flag is set, all project's members would be "
                  "notified by mail for all project's changes"),
    default = False,
))

config_register(StringValue(
    PROJECTOR,
    'TASK_EMAIL_SUBJECT_SUMMARY_FORMAT',
    description = _("Format of emails related with issues"),
    help_text = _("You may use following placeholders: $project $summary $id"),
    default = "$project - #$id: $summary",
))
'''

PROJECTOR = {
    'BASIC_AUTH_REALM': 'Projector Basic Auth',
    'MILESTONE_DEADLINE_DELTA': 60,
    'CHANGESETS_PAGINATE_BY': 10,
    #'PROJECT_EDITABLE_PERMISSIONS': [(codename, codename_to_label(codename))
    #    for codename in editable_perm_codenames],
    'PROJECT_EDITABLE_PERMISSIONS': editable_perm_codenames,
    'SEND_MAILS_USING_MAILER': False,
    'FROM_EMAIL_ADDRESS': settings.DEFAULT_FROM_EMAIL,
    'ALWAYS_SEND_MAILS_TO_MEMBERS': False,
    'TASK_EMAIL_SUBJECT_SUMMARY_FORMAT': "$project - #$id: $summary",
}

def get_config_value(key):
    return PROJECTOR[key]

