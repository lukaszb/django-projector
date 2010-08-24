"""
Unit tests for ``django-projector``

Won't run if we let setuptools to install dependancies inside current
directory - we need to install external packages before running test
suite.
"""
import os
import sys

os.environ["DJANGO_SETTINGS_MODULE"] = "example_project.settings_test"
from example_project import settings_test as settings

def main():
    sys.path.insert(0, os.path.abspath(os.path.curdir))
    from django.test.utils import get_runner
    test_runner = get_runner(settings)(verbosity=1)

    failures = test_runner.run_tests(['projector'])
    sys.exit(failures)

if __name__ == '__main__':
    main()

