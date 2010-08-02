"""
Exceptions raised by ``django-projector``. All error classes should extend
from one of those exceptions.
"""

class ProjectorError(Exception):
    """
    Main ``django-projector`` exception.
    """
    pass

class NotApplicableError(ProjectorError):
    pass

class NotRequestError(ProjectorError):
    pass

class ConfigAlreadyExist(ProjectorError):
    pass

