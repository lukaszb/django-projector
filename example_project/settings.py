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
    'djalog',
    'django_extensions',
    'django_sorting',
    'debug_toolbar',
    'guardian',
    'keyedcache',
    'pagination',
    'registration',
    'richtemplates',
    'signals_ahoy',
    'tagging',
    'projector',
    'vcs.web.simplevcs',
    'mailer',

    'example_project',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.transaction.TransactionMiddleware',

    'djalog.middleware.SQLLoggingMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'richtemplates.middleware.Http403Middleware',
    'django_sorting.middleware.SortingMiddleware',
    'vcs.web.simplevcs.middleware.PaginationMiddleware',
)

INTERNAL_IPS = ('127.0.0.1',)

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
#CACHE_TIMEOUT = 1 # For dev server

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
PROJECTOR_CREATE_PROJECT_ASYNCHRONOUSLY = False

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

# ====================== #
# DEBUG TOOLBAR SETTINGS #
# ====================== #

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}

# ================ #
# REQUEST SETTINGS #
# ================ #

REQUEST_IGNORE_PATHS = (
    r'^%s' % MEDIA_URL.lstrip('/'),
    r'^%s' % ADMIN_MEDIA_PREFIX.lstrip('/'),
)

# ============== #
# EMAIL SETTINGS #
# ============== #

DEFAULT_FROM_EMAIL = 'webmaster@localhost'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_HOST_PASSWORD = ''
EMAIL_HOST_USER = ''
EMAIL_PORT = 25
EMAIL_SUBJECT_PREFIX = '[Django] '
EMAIL_USE_TLS = False

try:
    from conf.local_settings import *
    try:
        for app in LOCAL_INSTALLED_APPS:
            if app not in INSTALLED_APPS:
                INSTALLED_APPS += (app,)
        for middleware in LOCAL_MIDDLEWARE_CLASSES:
            if middleware not in MIDDLEWARE_CLASSES:
                MIDDLEWARE_CLASSES += (middleware,)
    except NameError:
        pass
except ImportError:
    pass

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend', # this is default
    'guardian.backends.ObjectPermissionBackend',
)
ANONYMOUS_USER_ID = -1

