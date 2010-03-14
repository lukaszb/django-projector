import os
import logging
from django.conf import settings

abspath = lambda *p: os.path.abspath(os.path.join(*p))

USE_PYGMENTS = getattr(settings, 'PROJECTOR_USE_PYGMENTS', False)

HG_ROOT_DIR = getattr(settings, 'PROJECTOR_HG_ROOT_DIR', None)
if HG_ROOT_DIR is None:
    logging.debug("django-projector: HG_ROOT_DIR not set - "
        "will not create mercurial repositories")
else:
    HG_ROOT_DIR = abspath(HG_ROOT_DIR)
    if not os.path.exists(HG_ROOT_DIR):
        os.mkdir(HG_ROOT_DIR)
        logging.info("django-projector: created %s directory."
            % HG_ROOT_DIR)
HG_BASIC_AUTH_REALM = getattr(settings, 'PROJECTOR_HG_BASIC_AUTH_REALM', 'Projector Basic Auth')
HG_PUSH_SSL = getattr(settings, 'PROJECTOR_HG_PUSH_SSL', None)
if HG_PUSH_SSL is None:
    HG_PUSH_SSL = settings.DEBUG and 'false' or 'true'

BANNED_PROJECT_NAMES = getattr(settings, 'PROJECTOR_BANNED_PROJECT_NAMES', ())
BANNED_PROJECT_NAMES += (
    'accounts',
    'admin',
    'registration',
    'users',
    'create',
    'edit',
)
