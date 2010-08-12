from django.utils.importlib import import_module

def codename_to_label(codename):
    rremove = '_project'
    if codename.endswith(rremove):
        codename = codename[:len(codename)-len(rremove)]
    codename = codename\
        .split('.')[1]\
        .replace('_', ' ')\
        .capitalize()
    return codename

def str2obj(text):
    """
    Returns object pointed by the string. In example::

        >>> from projector.models import Project
        >>> point = 'projector.models.Project'
        >>> obj = str2obj(point)
        >>> obj is Project
        True

    """
    modpath, objname = text.rsplit('.', 1)
    mod = import_module(modpath)
    try:
        obj = getattr(mod, objname)
    except AttributeError:
        raise ImportError("Cannot retrieve object from location %s" % text)
    return obj

