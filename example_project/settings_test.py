from settings import *

# Make celery fire up tasks synchronously
CELERY_ALWAYS_EAGER = True

#PROJECTOR_CREATE_PROJECT_ASYNCHRONOUSLY = False
#PROJECTOR_SEND_MAIL_ASYNCHRONOUSELY = False
PROJECTOR_DEFAULT_PROJECT_WORKFLOW = 'projector.tests.workflow.TestWorkflow'
PROJECTOR_PROJECTS_HOMEDIR_GETTER = 'projector.tests.base.get_homedir'

# Hide logging messages
DJALOG_LEVEL = 50

