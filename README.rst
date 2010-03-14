================
django-projector
================

``django-projector`` is a project management application with task tracker
and repository backend integration. Aimed to work with upcoming, version
1.2 of Django_ framework. We are sick of Trac [1]_ and wanted to create
simple application which can be easily customized or plugged into
existing systems.

.. warning::
   This application is at early-development stage but we strongly encourage
   you to give it a try if you are looking for project management toolkit
   for your Django_ based project.

------------
Installation
------------

See http://packages.python.org/django-projector/installation.html
for information on installing ``django-projector``. It is also
available in ``docs`` directory at ``docs/installation.rst``.

-------------
Documentation
-------------

Online documentation for development version is available at
http://packages.python.org/django-projector/.

You may also build documentation for yourself but you would need Sphinx_
for that. Go into ``docs/`` and run::

   make html

-------
License
-------

``django-projector`` is released under MIT_ license. You should get a copy
of the license with source distribution, at the root location, within
``LICENSE`` file.

.. _Django: http://www.djangoproject.com/
.. _Trac: http://trac.edgewall.org/
.. _Sphinx: http://sphinx.pocoo.org/
.. _MIT: http://www.opensource.org/licenses/mit-license.php

.. [1] Don't get us wrong, Trac_ is great tool but we believe that
   django's pluggable applications are far easier to configure and
   deploy.
