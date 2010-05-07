import os
import logging

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from livesettings import config_register, StringValue, IntegerValue,\
    BooleanValue, ConfigurationGroup

from projector.utils.validators import IntegerValidator

abspath = lambda *p: os.path.abspath(os.path.join(*p))

BANNED_PROJECT_NAMES = getattr(settings, 'PROJECTOR_BANNED_PROJECT_NAMES', ())
BANNED_PROJECT_NAMES += (
    'accounts',
    'add',
    'admin',
    'api',
    'author', 'authors',
    'category', 'categories',
    'create',
    'edit',
    'issue', 'issues',
    'projects', 'projector',
    'register', 'registration',
    'task', 'tasks',
    'update',
    'user', 'users',
)

CREATE_PROJECT_ASYNCHRONOUSLY = getattr(settings,
    'PROJECTOR_CREATE_PROJECT_ASYNCHRONOUSLY', True)

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


# Following settings may be changed dynamically (livesettings)

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

