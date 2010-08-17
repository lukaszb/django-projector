.. _teamwork:

========
Teamwork
========

``django-projector`` is all about making life easier for project's members.
Thus, we try to implement the best practices in this area, and new proposals
are always welcome!

.. _teamwork-mappings:

Mappings
========

Most of the times within Django_ project we use ``django.contrib.auth``
application to store and manage users (:py:class:`auth.User`) and
groups (:py:class:`auth.Group`).

.. note::
   Note that we refer to model using standard notation ``app_label.ModelName``
   which is used around django community. We prefer that over typing full
   python path to the specific class.

Those are very simply models and give developers ability to wrap them around
they own classes. We use them too and this section describes how we do it at
``django-projector``.

Most important model within application is :py:class:`projector.Project`. We
connect it with users by :py:class:`projector.Membership` model. Moreover, we
also use :py:class:`projector.Team` - it provides connection between
:py:class:`projector.Project`, :py:class:`auth.User` and :py:class:`auth.Group`
models.

.. _teamwork-membership:

Membership
==========

Each user is related with project by :py:class:`projector.Membership` instance.

Administration
--------------

Membership for the author of the project is created automatically, and is given
all available permissions and thus it's member is referenced as project's
administrator.

Project's adminstrator can add new member, change permissions of existing ones
or remove members if necessary. Project owner's permissions cannot be changed.

Admin can also manage :ref:`teams <teamwork-team>`.

Other members
-------------

User may be project's *member* without associated
:py:class:`projector.Membership` instance if he or she is member of a
:py:class:`auth.Group` (by the instance of :py:class:`projector.Team` - see
:ref:`below <teamwork-team>` for more detail).

.. _teamwork-membership-anon:

AnonymousUser member
--------------------

Since Django_ 1.2 authentication backends may support anonymous user and 
django-guardian_ implements this functionality (see more at it's `documentation
<http://packages.python.org/django-guardian/configuration.html>`_). As so,
it is possible to add :py:class:`auth.AnonymousUser` as a project's member
and manage it's permissions as with any other user.

.. warning::
   It is possible to give out administration privileges to
   anonymous user this way. Some views (like task creation or project edition)
   requires user to be logged in but project's owner should be careful about
   anonymous user's permission management.


.. _teamwork-membership-convert:

Convert to ``Team``
-------------------

Any user may be converted into :py:class:`projector.Team` instance. Well, this
is not totally true - in fact, by conversion to ``Team`` we mean *set a team
flag* on the user's profile. Conversion is available if user profile's
``is_team`` attribute is False and there is no :py:class:`auth.Group` instance
named same as the user.

Conversion is done within user's dashboard and each step of conversion is
described below:

#. User clicks on *Convert to Team* button at his or her dashboard.

#. If there is :py:class:`auth.Group` named as the user, ``ValidationError`` is
   raised.

#. User confirms conversion.

#. :py:class:`auth.Group` instance named same as the user is created. This group
   is automatically added to ``User.groups``.

#. ``UserProfile.is_team`` attribute is set to ``True``. From now on, accessing
   ``UserProfile.group`` would return :py:class:`auth.Group` instance created in
   previous step.

Conversion's api is provided by :py:class:`projector.Team` manager's method
:py:meth:`projector.managers.TeamManager.convert_from_user`.

.. _teamwork-team:

Team
====

Any :py:class:`auth.Group` may be used to create :py:class:`projector.Team`
instance which bounds :py:class:`auth.Group` and :py:class:`projector.Project`.
Normally, one would create group using :ref:`account conversion
<teamwork-membership-convert>`.

One user may be member of many teams. Single project may be managed by many
users *and* many teams. It may be confusing but it's really simple.


.. _django: http://www.djangoproject.com/
.. _django-guardian: http://github.com/lukaszb/django-guardian/
