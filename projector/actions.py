from django.db.models.signals import post_save
from projector.models import Project

import logging

class ProjectAction(object):
    alias = "project_created"
    verb = "created"
    signal = post_save
    sender = Project

    @staticmethod
    def action(sender, instance, created, **kwargs):
        logging.debug("Sending ProjectAction")
        if created and instance.parent:
            instance.parent.create_action("forked", author=instance.author)
        elif created:
            instance.create_action("created")

    def connect_signal(self):
        self.signal.connect(ProjectAction.action, sender=ProjectAction.sender)


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
        ProjectAction,
    )
    for ActionClass in actions:
        action = ActionClass()
        action.connect_signal()

