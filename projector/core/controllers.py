from django.http import HttpRequest
from projector.exceptions import NotRequestError

class BaseView(object):
    """

    """
    def __new__(cls, request, *args, **kwargs):
        view = cls.new(request, *args, **kwargs)
        return view.__call__()

    @classmethod
    def new(cls, request, *args, **kwargs):
        obj = object.__new__(cls)
        obj.__init__(request, *args, **kwargs)
        if request is None or not isinstance(request, HttpRequest):
            raise NotRequestError("Class based views requires HttpRequest "
                "to be passed as first argument (got %s)" % request)
        obj.args = args
        obj.kwargs = kwargs
        return obj

    def __init__(self, request, *args, **kwargs):
        """
        Should be overridden, for example::

            def __init__(self, request, page_slug):
                self.request = request
                self.page_slug = page_slug

        """
        pass

    def __call__(self):
        raise NotImplementedError("BaseView subclasses should implement "
            "__call__ method (it should return django.http.HttpResponse)")

