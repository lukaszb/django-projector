import logging

from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator

from signals_ahoy.asynchronous import AsynchronousListener

from projector import settings as projector_settings
from projector.models import Project

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

def start_listening():
    post_save.connect(request_new_profile, sender=User)

    if projector_settings.CREATE_PROJECT_ASYNCHRONOUSLY:
        post_save.connect(async_project_created_listener.listen, sender=Project)
    else:
        post_save.connect(project_created_listener, sender=Project)

