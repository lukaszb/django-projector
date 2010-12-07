from django.contrib.auth.models import User
from django.db.models.signals import post_save

from projector.models import Project
from projector.models import Task

from vcs.web.simplevcs.models import Repository


def action_project_created(sender, instance, created, **kwargs):

    if created and instance.parent:
        instance.parent.create_action("forked", author=instance.author)
    elif created:
        instance.create_action("created", author=instance.author)


def action_task_saved(sender, instance, created, **kwargs):

    if created:
        instance.project.create_action("created new task",
            author=instance.editor, action_object=instance)
    else:
        try:
            last_rev = instance.taskrevision_set\
                .select_related('status')\
                .order_by('-created_at')[1]
            if instance.status.is_resolved and not last_rev.status.is_resolved:
                verb = "resolved"
            elif not instance.status.is_resolved and last_rev.status.is_resolved:
                verb = "reopened"
            else:
                verb = "updated"
            instance.project.create_action(verb, action_object=instance,
                author=instance.editor)
        except IndexError:
            pass


def pushed(sender, **kwargs):
    try:
        project = Project.objects\
            .select_related('repository')\
            .get(repository__path=kwargs.get('repo_path'))
        author = User.objects.get(username=kwargs.get('username'))
        verb = "pushed to"
        project.create_action(verb, author=author)
    except Project.DoesNotExist:
        pass
    except User.DoesNotExist:
        pass

def actions_start_listening():
    """
    Register handlers for users activity.
    """
    post_save.connect(action_project_created, sender=Project)
    post_save.connect(action_task_saved, sender=Task)

    from vcs.web.simplevcs.signals import post_push
    post_push.connect(pushed, sender=None)

