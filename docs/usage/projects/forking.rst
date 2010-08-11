.. _projects-forking:

=======
Forking
=======

Return to :ref:`projects`.

.. versionadded:: 0.1.8

In many situations we need to *clone* one project, make some changes
(*progress*), review them and eventually merge them into upstream. Or we know
that our changes won't be accepted (or shouldn't be) but we still need to make
them for our own reasons. When we talk about software repository we would call
that clone a *branch*. But if we refer to project as a whole, we often call this
projects' copies *forks*.

``django-projector`` allows user to fork another project not only within it's
own context. It is also possible to fork a project from external location,
i.e. from Bitbucket_.

.. _projects-forking-internal:

Internal fork
=============

This is standard fork functionality which may be found at other forges.
Procedure is simple:

1. Jack decides to fork project named *joe's project*
2. At the *joe's project* main page Jack clicks on *Fork* button
3. Jack is redirected to his new forked project named as original one

.. _projects-forking-external:

External fork
=============

At his or her dasboard, user can find a *Fork project* button. This does **not**
refer to :ref:`internal fork <projects-forking-internal>`. External forking
only allows to fork from external location.

To enable this functionality, it's necessary to set
``PROJECTOR_FORK_EXTERNAL_ENABLED = True`` at settings file. Moreover,
``PROJECTOR_FORK_EXTERNAL_MAP`` dict setting should be set properly (see
:ref:`configuration`).

.. warning::
   We **DO NOT** take any responsibility caused by using external forking.
   Reason is simple - some users could use this functionality to attack
   external hosts by sending crafted values to the fork form. Values should be
   validated by the form first, though.

How to write external fork form
-------------------------------

External fork form should subclass
:py:class:`projector.forks.base.BaseExternalForkForm` and implement ``fork``
method:

* ``fork(request)``: this method should implement action required to create
  :py:class:`projector.models.Project` instance. Note that real fork procedure
  is fired by project creation handler. We may create a project in whatever way
  we want here but most basic scenario is to pass ``author``, ``name`` and
  ``public`` attributes to the constructor of
  :py:class:`projector.models.Project` class.

  .. note::
     All exceptions at ``fork`` method should be caught and eventually
     propagated but with type ``projector.core.exceptions.ProjectError`` (or a
     subclass of it). It is necessary for
     :py:class:`projector.forms.ExternalForkWizard` to properly notify user
     if any error has occured during forking process. Those are not validation
     errors as ``fork`` method should be called only after form is cleaned.

Moreover, :py:class:`projector.forks.base.BaseExternalForkForm` comes with
one field ``as_private``. After form validation it is possible to check
if project should be forked as *public* or *private* by calling ``is_public``
form's method. This method would return ``True`` or ``False``.

After form is implemented we can hook it at the ``PROJECTOR_FORK_EXTERNAL_MAP``
setting.

We advice to review code of :py:mod:`projector.forks.bitbucket` module to see
full example.

.. _Bitbucket: http://bitbucket.org
