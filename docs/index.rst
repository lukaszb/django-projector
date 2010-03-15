.. django-projector documentation master file, created by
   sphinx-quickstart on Thu Feb 18 23:18:28 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to django-projector's documentation!
============================================

``django-projector`` project management application with task tracker
and repository backend integration. Aimed to work with upcoming, version
1.2 of Django_ framework. We are sick of Trac_ and wanted to create
simple application which can be easily customized or plugged into
existing systems.

.. image:: _static/django-projector-01.png
   :width: 760px

Features
--------

- Task tracker with full history of changes
- Mercurial_ repository integration
- Repository web browser (basic... really)
- Granual permissions management (see :ref:`authorization`)
- Documents based on `restructuredText`_
- Make use of `django-richtemplates`_ so templates are ready to use
  out of the box
- More to come

Incoming
--------

Here are some additional points which are the target for future
release.

- Wiki per project
- Other version control systems in backend (git_, subversion_...)
- Customizable workflow for each project
- Charts, statistics, graphs, plots, analyzies
- Functional roadmap/timeline
- Email notification
- `django-piston`_ integration

.. warning::
   This application is at early-development stage but we strongly encourage
   you to give it a try if you are looking for project management toolkit
   for your Django_ based project. Still, it probably should **NOT** be used
   in production as it wasn't fully tested and may contain security issues.

Documentation
=============

**Installation:**

.. toctree::
   :maxdepth: 1

   installation
   configuration
   authorization

Other topics
============

* :ref:`genindex`
* :ref:`search`

.. _django: http://www.djangoproject.com/
.. _django-richtemplates: http://bitbucket.org/lukaszb/django-richtemplates/
.. _django-piston: http://bitbucket.org/jespern/django-piston/
.. _restructuredText: http://docutils.sourceforge.net/rst.html
.. _mercurial: http://mercurial.selenic.com/
.. _subversion: http://subversion.tigris.org/
.. _git: http://git-scm.com/
.. _trac: http://trac.edgewall.org/
