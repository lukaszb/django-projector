.. _configuration:

=============
Configuration
=============

After you hook ``django-projector`` into your project (see :ref:`installation`)
you should probably change some of configuration variables.


.. setting:: ALL

Available settings
==================

Those configurable variables should be defined at the project's settings module,
just like standard `Django's variables
<http://docs.djangoproject.com/en/dev/ref/settings/#ref-settings>`_.

.. setting:: PROJECTOR_ALWAYS_SEND_MAILS_TO_MEMBERS

PROJECTOR_ALWAYS_SEND_MAILS_TO_MEMBERS
--------------------------------------

Default: ``False``

If set to ``True``, any change to project would send an email to each projects'
members regardless of their individual preferences.

.. setting:: PROJECTOR_BANNED_PROJECT_NAMES

PROJECTOR_BANNED_PROJECT_NAMES
------------------------------

Default::

    (
        'account', 'accounts',
        'add',
        'admin', 'admins',
        'api',
        'author', 'authors',
        'ban',
        'category', 'categories',
        'change',
        'create',
        'default',
        'delete',
        'edit', 'edits',
        'etc',
        'issue', 'issues',
        'mail', 'mails',
        'message', 'messages',
        'manager', 'managers',
        'private',
        'profile', 'profiles',
        'projects',
        'register', 'registration',
        'remove',
        'task', 'tasks',
        'update',
        'user', 'users',
        'view',
    )

List of names which are restricted during project creation.

.. note::
   By specifying own list, we in fact extend default list. We mention this as
   most of the settings are overridable - this one is not.

.. setting:: PROJECTOR_BASIC_AUTH_REALM

PROJECTOR_BASIC_AUTH_REALM
--------------------------

Default: ``'Projector Basic Auth'``

Text which would appear during basic authorization process within projector's
context. Projects' owners can override this *per project*.

.. setting:: PROJECTOR_CHANGESETS_PAGINATE_BY

PROJECTOR_CHANGESETS_PAGINATE_BY
--------------------------------

Default: ``10``

Number of changesets listed at one page.

.. setting:: PROJECTOR_CREATE_PROJECT_ASYNCHRONOUSLY

PROJECTOR_CREATE_PROJECT_ASYNCHRONOUSLY
---------------------------------------

Default: ``True``

When new project is created some actions are made using `Djangos' signals
<http://docs.djangoproject.com/en/dev/topics/signals/#topics-signals>`_.  By
default those actions are made asynchronousely by new thread in order not to
block client.

.. setting:: PROJECTOR_DEFAULT_PROJECT_WORKFLOW

PROJECTOR_DEFAULT_PROJECT_WORKFLOW
----------------------------------

Default: ``projector.conf.default_workflow``

Path to object defining default workflow for new projects.

Object must define following iterables: *components*, *task_types*, *priorities*
and *statuses*. Each one should contain dictionaries with following key/value
pairs:

- **components**: *name*
- **task_types**: *name*, *order*
- **priorities**: *name*, *order*
- **statuses**: *name*, *oder*, *is_resolved*, *is_initial*

See source code pointed by default value for more detail.


.. setting:: PROJECTOR_DEFAULT_VCS_BACKEND

PROJECTOR_DEFAULT_VCS_BACKEND
-----------------------------

Default: ``'hg'``

One of *aliases* specified at :setting:`PROJECTOR_ENABLED_VCS_BACKENDS`. See
`vcs's documentation`_ for available aliases.



.. setting:: PROJECTOR_EDITABLE_PERMISSIONS

PROJECTOR_EDITABLE_PERMISSIONS
------------------------------

Default::

    (
        'change_project',
        'change_config_project',
        'view_project',
        'can_read_repository',
        'can_write_to_repository',
        'can_change_description',
        'can_change_category',
        'can_add_task',
        'can_change_task',
        'can_delete_task',
        'can_view_tasks',
        'can_add_member',
        'can_change_member',
        'can_delete_member',
        'can_add_team',
        'can_change_team',
        'can_delete_team',
    )

List of permission codenames allowed to be edited by projects' owners.

.. note::
   Removing variables from this tuple (by setting own with subset of
   available permissions) would not affect permissions - it only tells
   projector to show forms for permission editing with specified
   codenames.


.. setting:: PROJECTOR_ENABLED_VCS_BACKENDS

PROJECTOR_ENABLED_VCS_BACKENDS
------------------------------

Default: ``[hg]``

Iterable of vcs_ *aliases*. To check what backends are available run::

    >>> import vcs
    >>> vcs.backends.BACKENDS.keys()
    ['hg']

See more at `vcs's documentation`_.


.. setting:: PROJECTOR_FORK_EXTERNAL_ENABLED

PROJECTOR_FORK_EXTERNAL_ENABLED
-------------------------------

Default: ``False``

If set to ``True`` users would be allowed to fork projects from external
locations (read more at :ref:`projects-forking-external`).

.. warning::
   We **DO NOT** take any responsibility caused by using external forking.
   Reason is simple - some users could use this functionality to attack
   external hosts by sending crafted values to the fork form. This should be
   validated by the form first, though.

.. setting:: PROJECTOR_FORK_EXTERNAL_MAP

PROJECTOR_FORK_EXTERNAL_MAP
---------------------------

Default::

    {
        'bitbucket.org': 'projector.forks.bitbucket.BitbucketForkForm',
    }

Dictionary of forms to be used for external forking. Keys would be used as
choices at the first step of external forking process. Values should be paths
to the fork form. Read more at :ref:`projects-forking-external`.

.. setting:: PROJECTOR_FROM_EMAIL_ADDRESS

PROJECTOR_FROM_EMAIL_ADDRESS
----------------------------

Default: would try to get value from ``settings.DEFAULT_FROM_EMAIL``.

Email address used as sender for all mails send by projector.

.. setting:: PROJECTOR_HIDDEN_EMAIL_SUBSTITUTION

PROJECTOR_HIDDEN_EMAIL_SUBSTITUTION
-----------------------------------

Default: ``'HIDDEN_EMAIL'``.

Used as default substitution for hidden emails while using
:py:func:`projector.templatetags.hide_email` filter (if no parameter is
specified).

.. setting:: PROJECTOR_MAX_PROJECTS_PER_USER

PROJECTOR_MAX_PROJECTS_PER_USER
-------------------------------

Default: ``50``

Specifies maximum number of projects one user may create.

.. setting:: PROJECTOR_MILESTONE_DEADLINE_DELTA

PROJECTOR_MILESTONE_DEADLINE_DELTA
----------------------------------

Default: ``60`` (60 days)

This is default value of time delta (in days) added to current date during
milestone creation.

.. setting:: PROJECTOR_MILIS_BETWEEN_PROJECT_CREATION

PROJECTOR_MILIS_BETWEEN_PROJECT_CREATION
----------------------------------------

Default: ``15000`` (15 seconds)

After user created a project, he/she need to wait for time specified with
this setting until another project may be created by him/her.

.. setting:: PROJECTOR_PRIVATE_ONLY

PROJECTOR_PRIVATE_ONLY
----------------------

Default: ``False``

If ``True`` then only *private* projects may be created. Does *not* affect
existing projects.


.. setting:: PROJECTOR_PROJECTS_ROOT_DIR

PROJECTOR_PROJECTS_ROOT_DIR
---------------------------

Default: ``None``

If not specified, no repositories would be created. Must be valid directory
path. 

.. setting:: PROJECTOR_PROJECTS_HOMEDIR_GETTER

PROJECTOR_PROJECTS_HOMEDIR_GETTER
---------------------------------

Default: :py:class:`projector.utils.helpers.get_homedir`

Location of the function which should return relative project path. In order to
calculate full path of homedir, :py:class:`projector.models.Project` calls
pointed function and appends result to the
:setting:`PROJECTOR_PROJECTS_ROOT_DIR` value.

It is possible to change this location and override function. It takes one
required ``project`` parameter - instance of
:py:class:`projector.models.Project`. Default implementation returns simply
stringified primary key of the given ``project``.

.. setting:: PROJECTOR_TASK_EMAIL_SUBJECT_SUMMARY_FORMAT

PROJECTOR_TASK_EMAIL_SUBJECT_SUMMARY_FORMAT
-------------------------------------------

Default::

    "[$project] #$id: $summary"

This is default subject format for messages related with tasks. Allows to move
name placeholders (``$project``, ``$id``, ``$summary``). All placeholders are
optional - but adviced, obviousely.



.. setting:: get_config_value

``get_config_value(key)``
=========================

.. autofunction:: projector.settings.get_config_value


.. _vcs: http://bitbucket.org/marcinkuzminski/vcs/
.. _vcs's documentation: http://packages.python.org/vcs/installation.html

