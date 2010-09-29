from settings import *

# Make celery fire up tasks synchronously
CELERY_ALWAYS_EAGER = True

PROJECTOR_DEFAULT_PROJECT_WORKFLOW = 'projector.tests.workflow.TestWorkflow'
PROJECTOR_PROJECTS_HOMEDIR_GETTER = 'projector.tests.base.get_homedir'
PROJECTOR_HG_PUSH_SSL = False

# Hide logging messages
DJALOG_LEVEL = 50

