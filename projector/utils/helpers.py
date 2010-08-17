def get_homedir(project):
    """
    Returns unique home directory path for each project. Returned path should be
    relative to :setting:`PROJECTOR_PROJECTS_ROOT_DIR`.

    :param project: instance of :py:class:`projector.models.Project`

    .. note ::
       This is simplest possible implementation but on the other hand returned
       value depends solely on the primary key of the given ``project``. It is
       important **not** to use other fields as they may change. Primary key
       should never be changed while even creation date (``created_at`` field)
       may be edited.

       For tests however, this is not acceptable as test runner
       rollbacks queries which should normally be committed. Rollbacks make ID
       value not stable - as we run more and more tests we always got projects
       with same id (starting with 1 for each test). That said, test runner
       must use other *project homedir generator*.

    Implementation::

        return str(project.pk)

    """
    return str(project.pk)

