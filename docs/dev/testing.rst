.. dev-testing::

Testing
=======

We decided that best way to test ``django-projector`` would be to use not
complicated, boundled example project. It means less maintainance as tests have
to be make within django context anyway. On the other hand, this also implies
that tests are run in specifically defined environment (django settings module)
so it may not always fit into real project. This is still little disadvantage
and less maintainance means less work before release.

.. dev-testing-how-to::

How to test
~~~~~~~~~~~

In order to run test suite we simply run::

   python setup.py test

This should invoke preparation process and fire up Django test runner.

