.. _projects-basics:

==========
The Basics
==========

Return to :ref:`projects`.


.. _projects-basics-create:

Creating projects
=================

As :model:`Project` is most important (for ``django-projector``) and rather
non-trival model we would like to present whole process of creating projects,
step by step. 

Let's create our first project::

    >>> from django.contrib.auth.models import User
    >>> from projector.models import Project
    >>> joe = User.objects.get(username='joe')
    >>> project = Project.objects.create(author=joe, name='foobar')

Now we need to add *metadata* for created project. This is done in a few steps:

- :ref:`projects-basics-create-set-memberships`
- :ref:`projects-basics-create-set-author-permissions`
- :ref:`projects-basics-create-create-workflow`
- :ref:`projects-basics-create-create-config`
- :ref:`projects-basics-create-create-repository`

.. _projects-basics-create-set-memberships:

``set_memberships``
-------------------

Now we need to add membership for the author and if he/she is a *team* we would
create a :model:`Team` instance binding :model:`Project` and ``auth.Group``.
We simply call ``set_memberships`` method which would do this for us::

    >>> project.members.all()
    []
    >>> project.set_memberships()
    >>> project.members.all()
    [<User: joe>]

.. _projects-basics-create-set-author-permissions:

``set_author_permissions``
--------------------------

After author become first member of the project he/she still cannot, i.e.
*change* the project::

    >>> joe.has_perm('projector.change_project', project)
    >>> False

.. note::
   At projector's views if requested user is author of the project, permissions
   are not checked at all. This is intenional, as less database hits is always
   better. On the other hand, if i.e. user would give project away to other
   user, he still should have all permissions - at least until new owner
   wouldn't took them from original author.

We can now set permissions::

    >>> project.set_author_permissions()
    >>> joe.has_perm('projector.change_project', project)
    >>> True

.. _projects-basics-create-set-create-workflow:

``create_workflow``
-------------------

Workflow is a set of statuses, components etc. for each project. Default set of
objects is pointed by :setting:`PROJECTOR_DEFAULT_PROJECT_WORKFLOW`. Workflow
itself may be modified for each project. We may pass a string pointing to the
python object or an object itself. Again, simply fire up the method::

    >>> project.create_workflow()


.. _projects-basics-create-create-config:

``create_config``
-----------------

Per project configuration is available at :model:`Config`. This model defines
all *changable* settings for each project all projects need one::

    >>> project.create_config()

.. _projects-basics-create-create-repository:

``create_repository``
---------------------

If :setting:`PROJECTOR_CREATE_REPOSITORIES` is set to ``True`` then we should
create repository for the project::

    >>> from projector.settings import get_config_value
    >>> if get_config_value('CREATE_REPOSITORIES'):
            project.create_repository()


.. _projects-basics-create-setup:

``setup``
---------

:model:`Project` comes with ``setup`` method which would call all preparation
methods at given instance. Is is possible to pass ``vcs_alias`` and ``workflow``
parameters but they are not required. So all of the above code may be called
with little less effort::

    >>> from django.contrib.auth.models import User
    >>> from projector.models import Project
    >>> joe = User.objects.get(username='joe')
    >>> project = Project.objects.create(author=joe, name='foobar')
    >>> project.setup()

.. _projects-basics-create-quick:
            
Using manager
=============

At previous section, :ref:`projects-basics-create`, we have seen that there
are some methods which should be called every time new :model:`Project` is
created. We can call :ref:`projects-basics-create-setup` method to make the
process less tedious. On the other hand it may be even better if we can
simply save :model:`Project` instance into database and call ``setup``
method asyncronously (if :setting:`CREATE_PROJECT_ASYNCHRONOUSLY` is set to
``True``).

``Project.objects.create_project``
----------------------------------

There is a special signal :signal:`setup_project` which is called by the
:manager:`ProjectManager`'s ``create_project`` method. It is preferred way
to create new :model:`Project`::

    >>> from django.contrib.auth.models import User
    >>> from projector.models import Project
    >>> joe = User.objects.get(username='joe')
    >>> project = Project.objects.create_project(author=joe, name='foobar')

We can also specify ``vcs_alias`` or ``workflow`` parameters directly::

    >>> project = Project.objects.create_project(author=joe, name='foobar', vcs_alias='hg', workflow=None)

