.. _authorization:

Authorization and permissions
=============================

This project management system aims to be used by small to middle companies.

Object-level permissions
------------------------

``django-projector`` make use of `django-guardian`_ to handle object-level
permissions. Check out it's `documentation
<http://packages.python.org/django-guardian/>`_ to see detailed information
on the topic.

Project permissions
-------------------

Following permissions are defined for each project:

- ``change_project``
- ``view_project``
- ``can_read_repository``
- ``can_write_to_repository``
- ``can_change_description``
- ``can_change_category``
- ``can_add_task``
- ``can_change_task``
- ``can_delete_task``
- ``can_view_tasks``
- ``can_add_member``
- ``can_change_member``
- ``can_delete_member``
- ``can_add_team``
- ``can_change_team``
- ``can_delete_team``

.. _django-guardian: http://github.com/lukaszb/django-guardian/
