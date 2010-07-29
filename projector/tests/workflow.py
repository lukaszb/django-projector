
class TestWorkflow(object):

    components = (
        {
            'name': u'global',
        },
    )

    task_types = (
        {
            'name': u'task',
            'order': 1,
        },
    )

    priorities = (
        {
            'name': u'minor',
            'order': 1,
        },
    )

    statuses = (
        {
            'name': u'new',
            'order': 1,
            'is_resolved': False,
            'is_initial': True,
        },
    )

