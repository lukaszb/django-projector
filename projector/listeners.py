import logging

from django.db.models.signals import post_save, post_delete
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _

from projector.settings import get_config_value
from projector.models import Project, Task, WatchedItem
from projector.signals import post_fork
from projector.signals import setup_project
from projector.tasks import setup_project as setup_project_task

from richtemplates.utils import get_user_profile_model

from vcs.web.simplevcs.signals import retrieve_hg_post_push_messages

def request_new_profile(sender, instance, **kwargs):
    """
    Creation of profile for new users
    """
    _UserProfile = get_user_profile_model()
    if _UserProfile is None:
        return
    profile, created = _UserProfile.objects.get_or_create(
        user=instance,
    )
    if created is True:
        logging.debug("Creating profile for %s ..." % instance)
        profile.activation_token = default_token_generator.make_token(instance)
        profile.save()
        logging.debug("Created profile's id: %s" % profile.id)

def setup_project_listener(sender, instance, vcs_alias=None,
        workflow=None, **kwargs):
    """
    Task ``setup_project`` for signals framework.
    """
    if get_config_value('CREATE_PROJECT_ASYNCHRONOUSLY'):
        func = setup_project_task.delay
    else:
        func = setup_project_task
    logging.info("Calling setup_project task for instance %s" % instance)
    return func(instance, vcs_alias, workflow)

def fork_done(sender, fork, **kwargs):
    """
    Action made after project is forked.
    """
    pass

def task_save_listener(sender, instance, **kwargs):
    """
    Action made after task is saved (created or updated).
    """
    if kwargs['created'] is True:
        # Task was created
        pass
    else:
        # Task was updated
        pass

def watcheditem_save_listener(sender, instance, **kwargs):
    if kwargs['created'] is True:
        logging.info("%s started watching %s" % (instance.user,
            instance.content_object))
    else:
        logging.info("%s already watching %s" % (instance.user,
            instance.content_object))

def watcheditem_delete_listener(sender, instance, **kwargs):
    logging.info("%s stopped watching %s" % (instance.user,
        instance.content_object))


def hg_extra_messages(sender, repository, **kwargs):
    """
    Adds extra messages appended to request after successful push
    to mercurial repository.
    """
    size = repository.info.size
    msg = _('Repository size: %s' % filesizeformat(size))
    sender.messages.append(msg)


def start_listening():
    """
    As listeners use projectors' models we need to connect signals after they
    are registered so it is implemented as function called at the end of models
    module.
    """
    post_save.connect(request_new_profile, sender=User)
    post_save.connect(task_save_listener, sender=Task)
    post_save.connect(watcheditem_save_listener, sender=WatchedItem)
    post_delete.connect(watcheditem_delete_listener, sender=WatchedItem)

    # Projector signals connection
    post_fork.connect(fork_done)
    setup_project.connect(setup_project_listener, sender=Project)
    #retrieve_hg_post_push_messages.connect(hg_extra_messages,
        #sender=None)

