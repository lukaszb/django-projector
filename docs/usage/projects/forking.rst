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
refer to :ref:`internal fork <projects-forking-internal>`.


.. _Bitbucket: http://bitbucket.org
