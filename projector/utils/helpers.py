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


class Choices(object):
    """
    Inspired by same object from Repocracy.
    """

    @classmethod
    def as_choices(cls):
        from django.utils.translation import ugettext as _
        keys = [key for key in dir(cls) if isinstance(getattr(cls, key), int)\
            and key.isupper()]
        slugs = dict((key, key.capitalize().replace('_', ' ')) for key in keys)
        choices = [(getattr(cls, key), _(slugs[key])) for key in keys]
        choices.sort()
        return choices

    @classmethod
    def as_dict(cls):
        return dict(cls.as_choices())

    @classmethod
    def as_json_choices(cls):
        choices = cls.as_dict()
        from django.utils.simplejson import dumps
        return dumps(choices)

