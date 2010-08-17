.. _api-signals:

=======
Signals
=======

Return to :ref:`api`.

Provided signals
================

``django-projector`` provides following signals:

.. signal:: post_fork

``post_fork``
-------------

After fork is done ``post_fork`` signal should be send.

``providing_args``:

+----------+-------------------------------------------------------------------+
| Name     | Description                                                       |
+==========+===================================================================+
| ``fork`` | Should be a :model:`Project` instance forked from another project |
+----------+-------------------------------------------------------------------+


.. signal:: setup_project

``setup_project``
-----------------

Should be send by :model:`Project` instance.

+---------------+-------------------------------------------------------+
| Name          | Description                                           |
+===============+=======================================================+
| ``instance``  | :model:`Project` instance which should be setup       |
+---------------+-------------------------------------------------------+
| ``vcs_alias`` | If given, would be used as backend for new repository |
+---------------+-------------------------------------------------------+
| ``workflow``  | If given, would override default workflow             |
+---------------+-------------------------------------------------------+


