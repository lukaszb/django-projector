"""
Project management Django application with task
tracker and repository backend integration.
"""

VERSION = (0, 1, 8)

__version__ = '.'.join((str(each) for each in VERSION[:4]))

def get_version():
    """
    Returns shorter version (digit parts only) as string.
    """
    return '.'.join((str(each) for each in VERSION[:3]))

