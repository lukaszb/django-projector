from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpRequest
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

login_required_m = method_decorator(login_required)

class BaseView(object):
    """
    Base class for django views.
    """
    login_required = False
    template_name = ''

    def __new__(cls, request, *args, **kwargs):
        if cls.login_required:
            cls.response = login_required_m(cls.response)
        view = cls.new(request, *args, **kwargs)
        return view.__call__()

    @classmethod
    def new(cls, request, *args, **kwargs):
        obj = object.__new__(cls)
        if not isinstance(request, HttpRequest):
            raise TypeError("Class based views requires HttpRequest "
                "to be passed as first argument (got %s)" % request)
        obj.request = request
        obj.context = {}
        obj.__init__(request, *args, **kwargs)
        obj.args = args
        obj.kwargs = kwargs
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

