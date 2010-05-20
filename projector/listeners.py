import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.contenttypes.models import ContentType

from signals_ahoy.asynchronous import AsynchronousListener

from projector import settings as projector_settings
from projector.models import Project, Task, WatchedItem
from projector.signals import messanger

from richtemplates.utils import get_user_profile_model
from vcs.web.simplevcs.models import Repository

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
    Could be heavy so should by handled asynchronously.
    """
    if not kwargs.get('created', False):
        # This listener is aimed for newly created projects only
        return
    if projector_settings.PROJECTS_ROOT_DIR:
        # Hardcoding repository creation process until more backends
        # are available from ``vcs``
        repo_path = instance._get_repo_path()
        alias = 'hg'
        logging.info("Initializing new mercurial repository at %s" % repo_path)
        repository = Repository.objects.create(path=repo_path, alias=alias)
        instance.repository = repository
        instance.create_workflow()
        instance.save()
    else:
        logging.debug("PROJECTOR_PROJECTS_ROOT_DIR is not set so we do NOT "
            "create repository for this project.")

async_project_created_listener = AsynchronousListener(project_created_listener)

def task_save_listener(sender, instance, **kwargs):
    """
    Action made after task is saved (created or updated).
    """
    if kwargs['created'] is True:
        # Task was created
        mail_info = {
            'subject': instance.get_long_summary,
            'body': instance.get_long_content,
            'recipient_list': [instance.author.email],
        }
        messanger.send(None, **mail_info)
    else:
        # Task was updated
        subject = instance.get_long_summary()
        body = instance.get_long_content()
        for watched_item in WatchedItem.objects.filter(
            content_type=ContentType.objects.get_for_model(Task),
            object_id = instance.pk):
            messanger.send(None,
                subject = subject,
                body = body,
                recipient_list = [watched_item.user.email])

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
        logging.info("%s started watching %s" % (instance.user, instance))
    else:
        logging.info("%s already watching %s" % (instance.user, instance))

def watcheditem_delete_listener(sender, instance, **kwargs):
    logging.info("%s stopped watching %s" % (instance.user, instance))

def start_listening():
    """
    As listeners use projectors' models we need to connect signals after they
    are registered so it is implemented as function called at the end of models
    module.
    """
    post_save.connect(request_new_profile, sender=User)
    post_save.connect(task_save_listener, sender=Task)
    post_save.connect(watcheditem_save_listener, sender=WatchedItem)
    post_save.connect(watcheditem_delete_listener, sender=WatchedItem)

    if projector_settings.CREATE_PROJECT_ASYNCHRONOUSLY:
        post_save.connect(async_project_created_listener.listen, sender=Project)
    else:
        post_save.connect(project_created_listener, sender=Project)

    if projector_settings.SEND_MAIL_ASYNCHRONOUSELY:
        messanger.connect(async_send_mail_listener.listen, sender=None)
    else:
        messanger.connect(send_mail_listener, sender=None)


