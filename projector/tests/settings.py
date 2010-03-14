from django.conf import global_settings

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}
INSTALLED_APPS = (
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
    'annoying',
    'attachments',
    'authority',
    'capo',
    'djalog',
    'django_extensions',
    'django_sorting',
    'notification',
    'pagination',
    'registration',
    'richtemplates',
    'rosetta',
    'tagging',
    'projector',

)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.transaction.TransactionMiddleware',

    'richtemplates.middleware.Http403Middleware',
    'django_sorting.middleware.SortingMiddleware',
    'djalog.middleware.SQLLoggingMiddleware',
    'projector.utils.simplehg.PaginationMiddleware',
)

DJALOG_LEVEL = logging.INFO
DJALOG_USE_COLORS = True
DJALOG_FORMAT = "[%(levelname)s] %(message)s"
ROOT_URLCONF = 'projector.tests.urls'
TEMPLATE_CONTEXT_PROCESSORS = global_settings + (
    #'django.core.context_processors.csrf',
    'django.core.context_processors.request',
)
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
    'django.template.loaders.eggs.load_template_source',
)

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), 'templates'),
    os.path.abspath(os.path.join(__import__('richtemplates').__path__[0],
        'templates_profiles', 'basic')),
)
SITE_ID = 1


