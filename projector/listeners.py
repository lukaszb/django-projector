import sys
import time
import logging
import datetime
import traceback

from django.db.models.signals import post_save, post_delete
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import mail_admins

from signals_ahoy.asynchronous import AsynchronousListener

from projector import settings as projector_settings
from projector.models import Project, Task, WatchedItem
from projector.signals import messanger, post_fork, setup_project
from projector.utils import str2obj

from richtemplates.utils import get_user_profile_model

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

def project_setup_listener(sender, instance, vcs_alias=None,
        workflow=None, **kwargs):
    """
    Creates all necessary related objects like statuses with transitions etc.
    It simply calls setup and we do this here as in a production it would most
    probably called asynchronously (with
    :setting:`PROJECTOR_CREATE_PROJECT_ASYNCHRONOUSLY` set to ``True``)

    :param instance: instance of :model:`Project`
    :param vcs_alias: alias of vcs backend
    :param workflow: object or string representing project workflow
    """
    if isinstance(workflow, str):
        workflow = str2obj(workflow)
    instance.setup(vcs_alias=vcs_alias, workflow=workflow)

def async_project_setup_listener(sender, instance, vcs_alias=None,
        workflow=None, **kwargs):
    """
    Project creation could be heavy so should by handled asynchronously.  On
    the other hand, new thread doesn't know if project has been already
    persisted or not - we need to check if it is available from database first.
    This problem may not be related with all databases (but is for i.e.
    PostgreSQL).
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

async_project_setup_listener = AsynchronousListener(
    async_project_setup_listener)

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
        setup_project.connect(async_project_setup_listener.listen,
            sender=Project)
    else:
        setup_project.connect(project_setup_listener, sender=Project)

    if projector_settings.SEND_MAIL_ASYNCHRONOUSELY:
        messanger.connect(async_send_mail_listener.listen, sender=None)
    else:
        messanger.connect(send_mail_listener, sender=None)

