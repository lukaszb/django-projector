.. django-projector documentation master file, created by
   sphinx-quickstart on Thu Feb 18 23:18:28 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to django-projector's documentation!
============================================

``django-projector`` is a project management application with task tracker and
repository backend integration. Aimed to work with Django_ 1.2 or later. We are
sick of Trac [1]_ and wanted to create simple application which can be easily
customized or plugged into existing systems.

.. image:: static/django-projector-01.png
   :width: 760px

Features
--------

- Task tracker with full history of changes
- Mercurial_ repository integration
- Repository web browser (basic... really)
- Customizable workflow for each project
- Grouping tasks in milestones
- Roadmap
- Granual permissions management (see :ref:`authorization`)
- Documents based on `restructuredText`_
- Make use of `django-richtemplates`_ so templates are ready to use
  out of the box
- Full project schema scripts (provided by `Capo`_)
- More to come

Incoming
--------

Here are some additional points which are the target for future
release.

- Wiki per project
- Other version control systems in backend (git_, subversion_...)
- Charts, statistics, graphs, plots, analyzies
- Functional timeline
- Email notification
- `django-piston`_ integration for RESTful API

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

**Usage:**

.. toctree::
   :maxdepth: 1

   example_project

**Development**

.. toctree::
   :maxdepth: 1

   dev/testing

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
.. _capo: http://bitbucket.org/lukaszb/capo/
