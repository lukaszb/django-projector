
class DefaultWorkflow(object):

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
        {
            'name': u'bug',
            'order': 2,
        },
        {
            'name': u'new feature',
            'order': 3,
        },
        {
            'name': u'proposal',
            'order': 4,
        },
    )

    priorities = (
        {
            'name': u'minor',
            'order': 1,
        },
        {
            'name': u'major',
            'order': 2,
        },
        {
            'name': u'critical',
            'order': 3,
        },
        {
            'name': u'blocker',
            'order': 4,
        },
    )

    statuses = (
        {
            'name': u'new',
            'order': 1,
            'is_resolved': False,
            'is_initial': True,
        },
        {
            'name': u'assigned',
            'order': 2,
            'is_resolved': False,
            'is_initial': False,
        },
        {
            'name': u'need fix',
            'order': 3,
            'is_resolved': False,
            'is_initial': False,
        },
        {
            'name': u'need feedback',
            'order': 4,
            'is_resolved': False,
            'is_initial': False,
        },
        {
            'name': u'need unittest',
            'order': 5,
            'is_resolved': False,
            'is_initial': False,
        },
        {
            'name': u'fixed',
            'order': 6,
            'is_resolved': True,
            'is_initial': False,
        },
        {
            'name': u'closed',
            'order': 7,
            'is_resolved': True,
            'is_initial': False,
        },
        {
            'name': u'wrong',
            'order': 8,
            'is_resolved': True,
            'is_initial': False,
        },
    )

