import sys
import time
import logging
import datetime
import traceback

from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import mail_admins

from signals_ahoy.asynchronous import AsynchronousListener

from projector import settings as projector_settings
from projector.models import Project, Config, Task, WatchedItem
from projector.signals import messanger, post_fork

from richtemplates.utils import get_user_profile_model
from vcs.web.simplevcs.models import Repository
from vcs.exceptions import VCSError

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

def project_created_listener(sender, instance, **kwargs):
    """
    Creates all necessary related objects like statuses with transitions etc.
    """
    if kwargs['created'] is False:
        return

    repo_path = instance._get_repo_path()

    logging.info("Trying to initialize repository at %s" % repo_path)

    # Hardcoding repository creation process until more backends
    # are available from ``vcs``
    alias = 'hg'
    try:
        clone_url = None
        if instance.parent:
            # Attempt to fork internally
            clone_url = instance.parent._get_repo_path()
        elif instance.fork_url:
            # Attempt to fork from external location
            clone_url = instance.fork_url
        repository = Repository.objects.create(path=repo_path,
            alias=alias, clone_url=clone_url)
        instance.repository = repository
    except VCSError, err:
        traceback_msg = '\n'.join(traceback.format_exception(*(sys.exc_info())))
        if clone_url is not None:
            msg = "Couldn't clone repository. Original error was: %s" % err
        else:
            msg = "Couldn't create repository. Original error was: %s" % err
        msg = '\n\n'.join((msg, traceback_msg))
        logging.error(msg)

    instance.create_workflow()
    instance.save()
    Config.create_for_project(instance)

def async_project_created_listener(sender, instance, **kwargs):
    """
    Project creation could be heavy so should by handled asynchronously.  On
    the other hand, new thread doesn't know if project has been already
    persisted or not - we need to check if it is available from database first.
    """
    try:
        if not kwargs.get('created', False):
            # This listener is aimed for newly created projects only
            return
        if projector_settings.PROJECTS_ROOT_DIR:
            iter = 0
            while True:
                try:
                    if iter > 10:
                        raise Exception("Couldn't run post-save project script "
                                "(tried %s times)" % iter)
                    else:
                        iter += 1
                    instance = Project.objects.get(pk=instance.pk)
                    project_created_listener(sender, instance, **kwargs)
                except Project.DoesNotExist:
                    secs = 1
                    logging.info("Sleeping for %s second(s) while waiting for "
                                 " '%s' project to be persisted" %
                                 (secs, instance))
                    time.sleep(secs)
                else:
                    break
        else:
            logging.debug("PROJECTOR_PROJECTS_ROOT_DIR is not set so we do NOT "
                "create repository for this project.")
    except (MemoryError, KeyboardInterrupt):
        pass
    except Exception, err:
        # We need to notify about any serious error
        subject = "[Projector Dev] Project %s was not created!" % instance.name
        traceback_msg = '\n'.join(traceback.format_exception(*(sys.exc_info())))
        msg = [
            "Unexpected error occured while creating project.",
            "",
            "Project: %s" % instance.name,
            "Error: %s" % err,
            "Error time: %s" % datetime.datetime.now(),
            "",
            "Traceback:",
            "==========",
            "",
            traceback_msg]
        msg = '\n'.join(msg)
        mail_admins(subject, msg)

async_project_created_listener = AsynchronousListener(
    async_project_created_listener)

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

def send_mail_listener(sender, subject, body, recipient_list,
        from_address=projector_settings.get_config_value('FROM_EMAIL_ADDRESS'),
        **kwargs):
    if 'mailer' in settings.INSTALLED_APPS and \
        projector_settings.get_config_value('SEND_MAILS_USING_MAILER'):
        from mailer import send_mail
    else:
        from django.core.mail import send_mail
    send_mail(subject, body, from_address, recipient_list)
    logging.debug("Sent mail to %s" % recipient_list)

async_send_mail_listener = AsynchronousListener(send_mail_listener)

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

    post_fork.connect(fork_done)

    if projector_settings.CREATE_PROJECT_ASYNCHRONOUSLY:
        post_save.connect(async_project_created_listener.listen, sender=Project)
    else:
        post_save.connect(project_created_listener, sender=Project)

    if projector_settings.SEND_MAIL_ASYNCHRONOUSELY:
        messanger.connect(async_send_mail_listener.listen, sender=None)
    else:
        messanger.connect(send_mail_listener, sender=None)

