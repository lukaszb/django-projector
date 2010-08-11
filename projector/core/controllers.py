from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpRequest, HttpResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

login_required_m = method_decorator(login_required)

class View(object):
    """
    Class-based view allowing it's subclasses to return dictionary at
    ``response`` method. :py:class:`django.http.HttpResponse` may also be
    returned, as usual.
    """
    login_required = False
    template_name = 'base.html'

    def __new__(cls, request, *args, **kwargs):
        # Wraps response method with ``login_required`` decorator
        # if ``login_required`` attribute is set to ``True`` at the class
        if cls.login_required:
            cls.response = login_required_m(cls.response)
        view = cls.new(request, *args, **kwargs)

        # If already a HttpResponse we should propagate it
        if isinstance(view, HttpResponse):
            return view
        return view.__call__()

    @classmethod
    def new(cls, request, *args, **kwargs):
        obj = object.__new__(cls)
        if not isinstance(request, HttpRequest):
            raise TypeError(
            "Class based views requires HttpRequest to be passed as first "
            "argument (got %s)" % request)
        obj.request = request
        obj.args = args
        obj.kwargs = kwargs
        obj.context = {}
        # Call __before__ method
        before = obj.__before__()
        if isinstance(before, HttpResponse):
            return before
        obj.__init__(request, *args, **kwargs)
        return obj

    def __before__(self):
        """
        Method called just after class is created and all passed parameters are
        set on the class, so it is possible to access those attributes.

        If this method would return :py:class:`django.http.HttpResponse`
        instance, it would be propagated.
        """
        pass

    def __after__(self):
        """
        Method called at the final step of the view-class processing. If
        :py:class:`django.http.HttpResponse` instance is returned it is
        propagated to the view handler.

        .. note::
           Adding i.e. ``context`` at this stage is pointless - response
           should have been already prepared and changing ``context`` wouldn't
           change the response. ``__after__`` method should be implemented
           for other purposes, like checking status code of prepared response.
           Response object is available by accessing ``self._response``. This
           attribute is available **only** at this stage.
        """
        pass

    def __init__(self, request, *args, **kwargs):
        """
        May be overridden, for example::

            def __init__(self, request, page_slug):
                self.page_slug = page_slug

        """
        pass

    def __call__(self):
        """
        Should be overridden only for special cases as it runs ``__after__``
        method. By subclassing it is possible to change the order of method
        calls.
        """
        if self.args and self.kwargs:
            response = self.response(self.request, *self.args, **self.kwargs)
        elif self.args:
            response = self.response(self.request, *self.args)
        elif self.kwargs:
            response = self.response(self.request, **self.kwargs)
        else:
            response = self.response(self.request)

        # If response is a dict, then we have to trasform it into HttpResponse
        if isinstance(response, dict):
            response = render_to_response(self.template_name, response,
                RequestContext(self.request))
        self._response = response

        # Call __after__ method just before we return response
        after = self.__after__()
        if isinstance(after, HttpResponse):
            return after
        del self._response
        return response

    def response(self, request):
        return self.context

