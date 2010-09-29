import logging
import StringIO
import traceback

from celery.decorators import task

from django.utils.translation import ugettext as _

from projector.models import Project, State
from projector.utils import str2obj
from projector.settings import get_config_value

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
            instance.create_repository(vcs_alias=vcs_alias)
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
        stack = StringIO.StringIO()
        traceback.print_exc(file=stack)
        stacktrace = stack.getvalue()

        logging.error("Error during project setup. Last state was: %s\n"
                      "Stack:\n%s\n" % (current_state, stacktrace))
        Project.objects.filter(pk=instance.pk).update(
            error_text=user_error_text)

