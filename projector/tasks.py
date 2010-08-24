import sys
import logging

from celery.decorators import task

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.mail import mail_admins as django_mail_admins
from django.core.mail import mail_managers as django_mail_managers
from django.utils.translation import ugettext as _

from projector.models import Project, State
from projector.utils import str2obj
from projector.settings import get_config_value

@task
def send_mail(subject, message, from_email=None, recipient_list=None):
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL
    if recipient_list is None:
        return 0
    sent = EmailMessage(subject, message, from_email, recipient_list).send()
    logging.debug("%s | %s | mails sent: %d" % (subject, recipient_list, sent))
    return sent


@task
def mail_admins(subject, message, fail_silently=False, connection=None):
    """
    Wrapper for django build-in mail_admins function.
    """
    if not settings.ADMINS:
        logging.warn("No ADMINS defined at settings module: no mails send")
        return 0
    sent = django_mail_admins(subject, message, fail_silently, connection)
    return sent

@task
def mail_managers(subject, message, fail_silently=False, connection=None):
    """
    Wrapper for django build-in mail_admins function.
    """
    if not settings.MANAGERS:
        logging.warn("No ADMINS defined at settings module: no mails send")
        return 0
    sent = django_mail_managers(subject, message, fail_silently, connection)
    return sent

@task
def project_create_repository(instance, vcs_alias=None):
    if get_config_value('CREATE_REPOSITORIES'):
        instance.create_repository(vcs_alias)

@task
def setup_project(instance, vcs_alias=None, workflow=None):
    """
    Creates all necessary related objects like statuses with transitions etc.
    It simply calls setup and we do this here as in a production it would most
    probably be called asynchronously (if
    :setting:`PROJECTOR_CREATE_PROJECT_ASYNCHRONOUSLY` is set to ``True``)

    :param instance: instance of :model:`Project`
    :param vcs_alias: alias of vcs backend
    :param workflow: object or string representing project workflow
    """
    logging.debug("Task setup_project called for instance %s" % instance)
    if isinstance(workflow, str):
        workflow = str2obj(workflow)
    #instance.setup(vcs_alias=vcs_alias, workflow=workflow)

    # Prepare if parametrs are given. Otherwise assume that preparation
    # methods have been called already
    if vcs_alias:
        instance.set_vcs_alias(vcs_alias)
    if workflow:
        instance.set_workflow(workflow)

    current_state = instance.state
    # Fire up sub-actions
    try:
        # Membership & Team
        instance.set_memberships()
        current_state = State.MEMBERSHIPS_CREATED
        Project.objects.filter(pk=instance.pk).update(state=current_state)

        # Author permissions
        instance.set_author_permissions()
        current_state = State.AUTHOR_PERMISSIONS_CREATED
        Project.objects.filter(pk=instance.pk).update(state=current_state)

        instance.create_workflow()
        current_state = State.WORKFLOW_CREATED
        Project.objects.filter(pk=instance.pk).update(state=current_state)

        instance.create_config()
        current_state = State.CONFIG_CREATED
        Project.objects.filter(pk=instance.pk).update(state=current_state)

        if get_config_value('CREATE_REPOSITORIES'):
            # We spawn sub task here as creating repositories is most crucial
            # task durgin project setup
            result = project_create_repository.delay(instance)
            result.wait()
            current_state = State.REPOSITORY_CREATED
            Project.objects.filter(pk=instance.pk).update(state=current_state)

        current_state = State.READY
        Project.objects.filter(pk=instance.pk).update(state=current_state)

    except (MemoryError, KeyboardInterrupt):
        raise
    except Exception:
        try:
            from djangodblog.models import Error
            Error.objects.create_from_exception()
        except ImportError:
            pass
        Project.objects.filter(pk=instance.pk).update(state=State.ERROR)
        user_error_text = _("There were some crazy error during project setup "
                            "process")
        logging.error("Error during project setup. Last state was: %s\n"
                      "Info:\n%s\n" % (current_state, sys.exc_info()))
        Project.objects.filter(pk=instance.pk).update(
            error_text=user_error_text)

