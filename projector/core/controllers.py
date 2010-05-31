
class BaseView(object):
    """

    """
    def __new__(cls, request, *args, **kwargs):
        view = cls.new(request, *args, **kwargs)
        return view.__call__()

    @classmethod
    def new(cls, *args, **kwargs):
        obj = object.__new__(cls)
        obj.__init__(*args, **kwargs)
        return obj

    def __init__(self, request, *args, **kwargs):
        """
        Should be overriden, for example::

            def __init__(self, request, page_slug):
                self.request = request
                self.page_slug = page_slug

        """
        self.request = request
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        raise NotImplementedError()

