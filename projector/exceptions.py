class ProjectorError(Exception):
    pass

class NotApplicableError(ProjectorError):
    pass

class NotRequestError(ProjectorError):
    pass

class ConfigAlreadyExist(ProjectorError):
    pass

