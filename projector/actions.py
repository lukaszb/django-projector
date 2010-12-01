from django.db.models.signals import post_save
from projector.models import Project


def action_project_created(sender, instance, created, **kwargs):

    if created and instance.parent:
        instance.parent.create_action("forked", author=instance.author)
    elif created:
        instance.create_action("created")

def actions_start_listening():
    """
    Register handlers for users activity.
    """
    post_save.connect(action_project_created, sender=Project)

