"""
Exceptions raised by ``django-projector``.

All internal error classes should extend from one of those exceptions.

:error:`ProjectorError` should always be *top-level* exception class.
"""

class ProjectorError(Exception):
    """
    Main ``django-projector`` exception.
    """
    pass

class ConfigAlreadyExist(ProjectorError):
    pass

class ForkError(ProjectorError):
    pass

