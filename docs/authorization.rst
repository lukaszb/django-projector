.. _authorization:

Authorization and permissions
=============================

This project management system aims to be used by small to middle companies.

Object-level permissions
------------------------

``django-projector`` make use of `django-authority`_ to handle object-level
permissions. Check out it's `documentation
<http://packages.python.org/django-authority/>`_ to see detailed information
on the topic.

Project permissions
-------------------

Following permissions are defined for each project:

- ``view``
- ``add_member_to``
- ``delete_member_from``
- ``view_tasks_for``
- ``can_add_task_to``
- ``can_change_task_to``
- ``can_read_repository``
- ``can_write_repository``

.. note::
   ``django-authority`` adds suffix ``_project`` for each of this permissions.

.. _django-authority: http://bitbucket.org/jezdez/django-authority/
