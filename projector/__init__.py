"""
Project management Django application with task
tracker and repository backend integration.
"""
from projector.utils.package import get_current_revision

VERSION = (0, 2, 0)

_rev = get_current_revision()
if 'dev' in VERSION and _rev:
    VERSION += ('%s:%s' % _rev,)

__version__ = '.'.join((str(each) for each in VERSION[:4]))

def get_version():
    """
    Returns shorter version (digit parts only) as string.
    """
    return '.'.join((str(each) for each in VERSION[:3]))

