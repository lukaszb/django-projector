import os
import sys

from django.conf import global_settings

abspath = lambda *p: os.path.abspath(os.path.join(*p))

DEBUG = True

PROJECT_ROOT = abspath(os.path.dirname(__file__))
PROJECTOR_MODULE_PATH = abspath(PROJECT_ROOT, '..')
sys.path.insert(0, PROJECTOR_MODULE_PATH)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': abspath(PROJECT_ROOT, '.hidden.db'),
        'TEST_NAME': ':memory:',
    },
}

# Make sqlite3 files relative to project's directory
for db, conf in DATABASES.items():
    if conf['ENGINE'] == 'sqlite3' and not conf['NAME'].startswith(':'):
        conf['NAME'] = abspath(PROJECT_ROOT, conf['NAME'])

INSTALLED_APPS = (
    'admin_tools',
    'admin_tools.theming',
    'admin_tools.menu',
    'admin_tools.dashboard',

    'native_tags',

    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.comments',
    'django.contrib.markup',
    'django.contrib.messages',
    'django.contrib.webdesign',

    # External
    'attachments',
    'authority',
    'dajax',
    'dajaxice',
    'djalog',
    'django_extensions',
    'django_sorting',
    'keyedcache',
    'livesettings',
    'pagination',
    'registration',
    'richtemplates',
    'signals_ahoy',
    'tagging',
    'projector',
    'projector.extras.users',
    'request',
    'vcs.web.simplevcs',
    'mailer',
    'gunicorn',

    'example_project',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.transaction.TransactionMiddleware',

    'richtemplates.middleware.Http403Middleware',
    'django_sorting.middleware.SortingMiddleware',
    'djalog.middleware.SQLLoggingMiddleware',
    'vcs.web.simplevcs.middleware.PaginationMiddleware',
)

MEDIA_ROOT = abspath(PROJECT_ROOT, 'media')
MEDIA_URL = '/media/'
ADMIN_MEDIA_PREFIX = '/admin-media/'

ROOT_URLCONF = 'example_project.urls'

TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS + (
    'django.core.context_processors.request',
    'richtemplates.context_processors.media',
)
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
    'django.template.loaders.eggs.load_template_source',
)

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), 'templates'),
)

SITE_ID = 1

USE_I18N = True
USE_L10N = True

CACHE_PREFIX = 'projector-example-project'
CACHE_TIMEOUT = 1 # For dev server

LOGIN_REDIRECT_URL = '/projector/'
AUTH_PROFILE_MODULE = 'projector.UserProfile'

TEST_RUNNER = 'django.test.simple.DjangoTestSuiteRunner'

# ================== #
# PROJECTOR SETTINGS #
# ================== #

PROJECTOR_PROJECTS_ROOT_DIR = abspath(
    PROJECT_ROOT, 'projects')
PROJECTOR_BANNED_PROJECT_NAMES = ('barfoo',)
PROJECTOR_SEND_MAIL_ASYNCHRONOUSELY = True
PROJECTOR_CREATE_PROJECT_ASYNCHRONOUSLY = True

# =============== #
# DJALOG SETTINGS #
# =============== #

DJALOG_SQL = True
DJALOG_SQL_SUMMARY_ONLY = True
DJALOG_LEVEL = 5
DJALOG_USE_COLORS = True
DJALOG_FORMAT = "[%(levelname)s] %(message)s"

# ====================== #
# RICHTEMPLATES SETTINGS #
# ====================== #

RICHTEMPLATES_RESTRUCTUREDTEXT_DIRECTIVES = {
    'code-block': 'richtemplates.rstdirectives.pygments_directive',
}
RICHTEMPLATES_DEFAULT_SKIN = 'ruby'
RICHTEMPLATES_PYGMENTS_STYLES = {
    'irblack': 'richtemplates.pygstyles.irblack.IrBlackStyle',
}

# ==================== #
# NATIVE_TAGS SETTINGS #
# ==================== #

NATIVE_TAGS = (
    'richtemplates.templatetags.native',
    'projector.templatetags.native',
)

# ================ #
# REQUEST SETTINGS #
# ================ #

REQUEST_IGNORE_PATHS = (
    r'^%s' % MEDIA_URL.lstrip('/'),
    r'^%s' % ADMIN_MEDIA_PREFIX.lstrip('/'),
)

try:
    from conf.local_settings import *
except ImportError:
    pass

