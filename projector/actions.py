from django.db.models.signals import post_save
from projector.models import Project

import logging


class ProjectorBaseAction(object):
    """
    Base Action class. Must define following attributes:

    ``alias``: unique identifier of this action

    ``verb``: short action's verb

    ``signal``: signal with which this action would be connected

    ``sender``: sender class or object

    Action classes must implement required, static method called ``action``
    which in fact is standard Django signal handler.
    """

    @staticmethod
    def action(sender, **kwargs):
        raise NotImplementedError

    @classmethod
    def connect_signal(cls):
        cls.signal.connect(cls.action, sender=cls.sender)


class ProjectCreatedAction(ProjectorBaseAction):
    alias = "project_created"
    verb = "created"
    signal = post_save
    sender = Project

    @staticmethod
    def action(sender, instance, created, **kwargs):
        logging.debug("Sending ProjectAction")
        if created and not instance.parent:
            instance.create_action(ProjectCreatedAction.verb)


class ProjectForkedAction(ProjectorBaseAction):
    alias = "project_forked"
    verb = "forked"
    signal = post_save
    sender = Project

    @staticmethod
    def action(sender, instance, created, **kwargs):
        if created and instance.parent:
            instance.parent.create_action(ProjectForkedAction.verb,
                author=instance.author)


def action_project_created(sender, instance, created, **kwargs):

    import ipdb; ipdb.set_trace()
    if created and instance.parent:
        instance.parent.create_action("forked", author=instance.author)
    elif created:
        instance.create_action("created")

def action_fork_created(sender, fork, **kwargs):
    sender.create_action(fork.author, "forked", action_object=sender)

def actions_start_listening():
    """
    Register handlers for users activity.
    """
    #post_save.connect(action_project_created, sender=Project)
    actions = (
        ProjectCreatedAction,
        ProjectForkedAction,
    )
    for cls in actions:
        cls.connect_signal()

