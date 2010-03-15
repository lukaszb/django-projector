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
- ``view_members``
- ``add_member``
- ``change_member``
- ``delete_member``
- ``view_tasks``
- ``add_task``
- ``change_task``
- ``read_repository``
- ``write_repository``

.. note::
   ``django-authority`` adds suffix ``_project`` for each of this permissions.

.. _django-authority: http://bitbucket.org/jezdez/django-authority/
