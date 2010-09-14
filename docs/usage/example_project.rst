.. _example-project:

Example projector-based project
===============================

.. versionadded:: 0.1.7

We have included example project for ``django-projector`` and it can be found
at (surprise!) ``example_project`` directory within both repository and source
release. As ``django-projector`` has many dependancies (see :ref:`installation`)
it may be hard to start at the first glance but this sample project can be used
as entry point.

.. note::
   We use example project to run :ref:`tests <dev-testing>`.

In order to run example project we need to make some preparation first.

Prepare
~~~~~~~

Step 1 - media files
--------------------

When specifing commands we assume we are at ``example_project`` directory.
Before we can run example project we need to include media files. Thanks to
`django-richtemplates`_ this is as easy as running one management command::

    python manage.py import_media richtemplates projector

This would fetch all necessary media files and put them into ``MEDIA_ROOT``
defined at settings module.

Step 2 - database
-----------------

Now we need to create database (we use ``sqlite3`` backend for sample project).
Type following command::

    python manage.py syncdb

Step 3 - fire up a worker
-------------------------

We need to run a celery worker for some heavy jobs to be done asynchronously.
As we use celery_ we need to start it at one terminal::

    python manage.py celeryd -l DEBUG


Step 4 - finalize
-----------------

In fact there is no step 4 - simply run development server::

    python manage.py runserver

... and open ``http://localhost:8000`` location in a browser.

.. _celery: http://celeryproject.org/
.. _django-richtemplates: http://bitbucket.org/lukaszb/django-richtemplates/

