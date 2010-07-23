from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpRequest

class BaseView(object):
    """
    Base class for django views.
    """
    def __new__(cls, request, *args, **kwargs):
        view = cls.new(request, *args, **kwargs)
        return view.__call__()

    @classmethod
    def new(cls, request, *args, **kwargs):
        obj = object.__new__(cls)
        if not isinstance(request, HttpRequest):
            raise TypeError("Class based views requires HttpRequest "
                "to be passed as first argument (got %s)" % request)
        else:
            obj.request = request
        obj.__init__(request, *args, **kwargs)
        obj.args = args
        obj.kwargs = kwargs
        obj.context = {}
        return obj

    def __init__(self, request, *args, **kwargs):
        """
        May be overridden, for example::

            def __init__(self, request, page_slug):
                self.request = request
                self.page_slug = page_slug

        """
        pass

    def __call__(self):
        if self.args and self.kwargs:
            response = self.response(self.request, *self.args, **self.kwargs)
        elif self.args:
            response = self.response(self.request, *self.args)
        elif self.kwargs:
            response = self.response(self.request, **self.kwargs)
        else:
            response = self.response(self.request)
        return response

    def response(self, request):
        raise NotImplementedError("BaseView subclasses should implement "
            "__call__ method (it should return django.http.HttpResponse)")

class View(BaseView):

    def __call__(self):

        response = super(View, self).__call__()

        if isinstance(response, dict):
            return render_to_response(self.template_name, response,
                RequestContext(self.request))
        return response

    def response(self, request):
        return {}

