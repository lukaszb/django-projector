.. _configuration:

Configuration
=============

After you hook ``django-projector`` into your project [1]_
you should probably change some of configuration variables.

Available settings
==================

Those configurable variables should be defined at the project's settings module,
just like standard `Django's variables <http://docs.djangoproject.com/en/dev/ref/settings/#ref-settings>`_.

PROJECTOR_ALWAYS_SEND_MAILS_TO_MEMBERS
--------------------------------------

Default: ``False``

If set to ``True``, any change to project would send an email to each projects'
members regardless of their individual preferences.

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

PROJECTOR_BASIC_AUTH_REALM
--------------------------

Default: ``'Projector Basic Auth'``

Text which would appear during basic authorization process within projector's
context. Projects' owners can override this *per project*.

PROJECTOR_CHANGESETS_PAGINATE_BY
--------------------------------

Default: ``10``

Number of changesets listed at one page.

PROJECTOR_CREATE_PROJECT_ASYNCHRONOUSLY
---------------------------------------

Default: ``True``

When new project is created some actions are made using `Djangos' signals <http://docs.djangoproject.com/en/dev/topics/signals/#topics-signals>`_.
By default those actions are made asynchronousely by new thread in order not to
block client.

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


PROJECTOR_MAX_PROJECTS_PER_USER
-------------------------------

Default: ``50``

Specifies maximum number of projects one user may create.

PROJECTOR_MILESTONE_DEADLINE_DELTA
----------------------------------

Default: ``60`` (60 days)

This is default value of time delta (in days) added to current date during
milestone creation.

PROJECTOR_MILIS_BETWEEN_PROJECT_CREATION
----------------------------------------

Default: ``15000`` (15 seconds)

After user created a project, he/she need to wait for time specified with
this setting until another project may be created by him/her.

PROJECTOR_PRIVATE_ONLY
----------------------

Default: ``False``

If ``True`` then only *private* projects may be created. Does *not* affect
existing projects.

PROJECTOR_PROJECTS_ROOT_DIR
---------------------------

Default: ``None``

If not specified, no repositories would be created. Must be valid directory
path. 

PROJECTOR_SEND_MAILS_USING_MAILER
---------------------------------

Default: ``False``

If ``True``, would try to use ``django-mailer`` instead of build in mail
sending functions.

PROJECTOR_TASK_EMAIL_SUBJECT_SUMMARY_FORMAT
-------------------------------------------

Default::

    "[$project] #$id: $summary"

This is default subject format for messages related with tasks. Allows to move
name placeholders (``$project``, ``$id``, ``$summary``). All placeholders are
optional - but adviced, obviousely.


.. [1] See :ref:`installation`
