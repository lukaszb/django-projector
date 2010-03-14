from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages

projector = __import__('projector')

def find_package_data():
    import os
    data_extensions = ['html', 'js', 'png', 'css', 'xml']
    data = {'projector': []}
    topdir = 'projector'
    for dir, subdirs, files in os.walk(topdir):
        for file in files:
            ext = file.split('.')[-1].lower()
            if ext in data_extensions:
                fpath = os.path.join(dir, file)[len('projector/'):]
                data['projector'].append(fpath)
    return data

setup(
    name = 'django-projector',
    version = projector.__version__,
    url = 'http://bitbucket.org/lukaszb/django-projector/',
    author = 'Lukasz Balcerzak',
    author_email = 'lukasz.balcerzak@python-center.pl',
    description = projector.__doc__,
    long_description = open('README.rst').read(),
    zip_safe = False,
    packages = find_packages(),
    include_package_data = True,
    package_data = find_package_data(),
    scripts = [],
    requires = ['Djalog', 'richtemplates', 'mercurial'],
    install_requires = [
        'djalog',
        'django-richtemplates',
        'mercurial',
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

