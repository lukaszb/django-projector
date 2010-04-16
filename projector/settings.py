import os
import logging
from django.conf import settings

abspath = lambda *p: os.path.abspath(os.path.join(*p))

USE_PYGMENTS = getattr(settings, 'PROJECTOR_USE_PYGMENTS', False)

BASIC_AUTH_REALM = getattr(settings, 'PROJECTOR_BASIC_AUTH_REALM',
    'Projector Basic Auth')

BANNED_PROJECT_NAMES = getattr(settings, 'PROJECTOR_BANNED_PROJECT_NAMES', ())
BANNED_PROJECT_NAMES += (
    'accounts',
    'admin',
    'registration',
    'users',
    'create',
    'edit',
)

PROJECTS_ROOT_DIR = getattr(settings, 'PROJECTOR_PROJECTS_ROOT_DIR', None)
if PROJECTS_ROOT_DIR is None:
    logging.debug("django-projector: RICHTEMPLATES_PROJECTS_ROOT_DIR not set "
        "- will not create repositories")
else:
    PROJECTS_ROOT_DIR = abspath(PROJECTS_ROOT_DIR)
    if not os.path.exists(PROJECTS_ROOT_DIR):
        os.mkdir(PROJECTS_ROOT_DIR)
        logging.info("django-projector: created %s directory"
            % PROJECTS_ROOT_DIR)

DEFAULT_DEADLINE_DELTA = 60 # In days

ALWAYS_ALLOW_READ_PUBLIC_PROJECTS = getattr(settings,
    'PROJECTOR_ALWAYS_ALLOW_READ_PUBLIC_PROJECTS', False)

