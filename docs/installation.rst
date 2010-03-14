.. _installation:

Installation
============

``django-projector`` is aimed to work with Django 1.2 which is going to be
released in march 2010. Till then you would need to use alpha/beta/trunk of
Django. Moreover, I strongly suggest to use ``virtualenv`` and
``virtualenvwrapper`` - great tools for creating temporary environment to work
on.

.. note::
    Well, in fact, as the time of writing only ``messages`` application is
    used from new Django_ version. And to use this new application you can
    simply copy ``django/contrib/messages`` folder into working installation
    of Django on your system.

Requirements
------------

Following packages are needed to get ``django-projector`` working:

- `Django`_ >= 1.2
- `django-authority`_
- `django-annoying`_
- `django-attachments`_
- `django-extensions`_
- `django-pagination`_
- `django-richtemplates`_
- `django-sorting`_
- `django-tagging`_
- `docutils`_
- `Pygments`_
- `Mercurial`_ >= 1.5


.. [1] `pip <http://pip.openplans.org/>`_ is tool similar to `easy_install
    <http://pypi.python.org/pypi/setuptools>`_ with some more power (like smooth
    integration with `virtualenv <http://virtualenv.openplans.org/>`_, ``freeze``
    command, package uninstallation and others.

.. _django: http://www.djangoproject.com
.. _django-authority: http://bitbucket.org/jezdez/django-authority/
.. _django-annoying: http://bitbucket.org/offline/django-annoying/
.. _django-attachments: http://github.com/bartTC/django-attachments 
.. _django-extensions: http://code.google.com/p/django-command-extensions/
.. _django-pagination: http://code.google.com/p/django-pagination/
.. _django-richtemplates: http://bitbucket.org/lukaszb/richtemplates/
.. _django-sorting: http://github.com/directeur/django-sorting
.. _django-tagging: http://code.google.com/p/django-tagging/
.. _docutils: http://docutils.sourceforge.net/
.. _pygments: http://pygments.org/
.. _mercurial: http://mercurial.selenic.com/
