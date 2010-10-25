"""
Help utilities for django-projector package.
"""
import os
import logging

def get_current_revision():
    """
    Returns tuple of (number, id) from repository containing this package
    or None if repository could not be found.
    """
    try:
        from vcs import get_repo
        from vcs.utils.helpers import get_scm
        from vcs.exceptions import RepositoryError, VCSError
        repopath = os.path.join(os.path.dirname(__file__), '..', '..')
        scm = get_scm(repopath)[0]
        repo = get_repo(path=repopath, alias=scm)
        tip = repo.get_changeset()
        return (tip.revision, tip.id)
    except (ImportError, RepositoryError, VCSError), err:
        logging.debug("Cannot retrieve projector's revision. Original error "
                      "was: %s" % err)
        return None

