import sys

from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages

projector = __import__('projector')
readme_file = 'README.rst'
try:
    long_description = open(readme_file).read()
except IOError, err:
    sys.stderr.write("[ERROR] Cannot find file specified as "
        "``long_description`` (%s)\n" % readme_file)
    sys.exit(1)

setup(
    name = 'django-projector',
    version = projector.__version__,
    url = 'http://www.django-projector.org',
    author = 'Lukasz Balcerzak',
    author_email = 'lukasz.balcerzak@python-center.pl',
    description = projector.__doc__,
    long_description = long_description,
    zip_safe = False,
    packages = find_packages(),
    include_package_data = True,
    scripts = [],
    requires = ['Djalog', 'richtemplates', 'mercurial'],
    install_requires = [
        'djalog',
        'django-richtemplates',
        'django-pagination>=1.0.7',
        'django-autoslug',
        'django-celery',
        'django-guardian',
        'django-registration',
        'docutils',
        'south',
    ],
    classifiers = ['Development Status :: 4 - Beta',
                   'Environment :: Web Environment',
                   'Framework :: Django',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
    ],
    test_suite='tests.main',
)

