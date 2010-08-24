.. _dev-testing:

Testing
=======

We decided that best way to test ``django-projector`` would be to use not
complicated, boundled :ref:`example project <example-project>`. It means less
maintainance as tests have to be make within django context anyway. On the
other hand, this also implies that tests are run in specifically defined
environment (django settings module) so it may not always fit into real
project. This is still little disadvantage and less maintainance means less
work before release.

.. _dev-testing-how-to:

How to test
~~~~~~~~~~~

In order to run test suite we simply run::

   python setup.py test

This should invoke preparation process and fire up Django test runner.

.. note::
   It is also possible to run test suite using management command but please
   remember that we have to use some custom settings and therefor it is
   **required** to use ``example_project/settings_test.py``. Simply run
   following command within example project::

      $ python manage.py test projector --settings=settings_test

