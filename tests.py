"""
Unit tests for ``django-projector``.
"""
import os
import sys

os.environ["DJANGO_SETTINGS_MODULE"] = "example_project.settings"
from example_project import settings

# Hide logging messages
settings.DJALOG_LEVEL = 30

def main():
    from django.test.utils import get_runner
    test_runner = get_runner(settings)(verbosity=1)

    failures = test_runner.run_tests(['projector'])
    sys.exit(failures)

if __name__ == '__main__':
    main()

