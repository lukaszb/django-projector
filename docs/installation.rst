.. _installation:

Installation
============

``django-projector`` is aimed to work with Django 1.2 or later. Moreover, we
strongly suggest to use `virtualenv`_ and `virtualenvwrapper`_ - great tools
for creating temporary environment to work on.

Requirements
------------

Requirements should be installed along with projector itself by the setuptools.
There is also ``requirements.txt`` file at the root of source distribution with
all needed packages. To install dependencies one should run pip [1]_ command::

    pip install -r requirements.txt

Trying it out
-------------

``django-projector`` comes with boundled example project. It can be easily used
- refer to :ref:`this document <example-project>` for more details.

.. [1] `pip <http://pip.openplans.org/>`_ is tool similar to `easy_install
    <http://pypi.python.org/pypi/setuptools>`_ with some more power (like
    smooth integration with `virtualenv <http://virtualenv.openplans.org/>`_,
    ``freeze`` command, package uninstallation, search and others.

.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _virtualenvwrapper: http://pypi.python.org/pypi/virtualenvwrapper

