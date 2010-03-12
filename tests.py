"""
Unit tests for ``django-projector``.
"""
import os
import sys
import logging

os.environ["DJANGO_SETTINGS_MODULE"] = "django.conf.global_settings"
from django.conf import global_settings

global_settings.DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}
global_settings.INSTALLED_APPS = (
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

global_settings.MIDDLEWARE_CLASSES = (
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

global_settings.DJALOG_LEVEL = logging.INFO
global_settings.DJALOG_USE_COLORS = True
global_settings.DJALOG_FORMAT = "[%(levelname)s] %(message)s"

def main():
    from django.test.utils import get_runner
    test_runner = get_runner(global_settings)(verbosity=1)

    failures = test_runner.run_tests(['projector'])
    sys.exit(failures)

if __name__ == '__main__':
    main()

