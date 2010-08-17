"""
This module extends standard Django function views and allows us to use *so
called* class-based-views. Django itself contains many features to power up
class based approach to the topic (for instance
``django.utils.decorators.method_decorator``).

During development of ``django-projector`` we just copied codes much too often
and class-based views allow us to complete many tasks in a much simpler way.
"""
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpRequest, HttpResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

login_required_m = method_decorator(login_required)

class View(object):
    """
    Main view class. Implemntation is focused around ``__call__`` method and
    *classmethod* ``new``.

    Subclasses should implement ``response`` method but it is not required.

    **Class-level attributes**:

    :attribute login_required:
        Default: ``False``.
        If set to ``True``, ``response`` method would be wrapped with standard
        ``django.contrib.auth.decorators.login_required``.

    :attribute template_name:
        Default: ``'base.html'``
        If ``response`` method returns a ``dict`` then this value is used to
        render context.

    **Instance-available attributes**:

    :attribute self.context:
        Context dictionary. During initialization it is set to empty dict
        (``{}``).

    :attribute self.request:
        ``django.http.HttpRequest`` instance passed in by the url resolver.

    :attribute self.args:
        Positional parameters passed in by url resolver.

    :attribute self.kwargs:
        Named parameters passed in by url resolver.

    **Implementation example**::

        from projector.core.controllers import View
        from projector.models import Project

        class ProjectList(View):

            login_required = True
            template_name = 'project_list.html'

            def response(self, request):
                self.context = Project.objects.all()
                return self.context

        class ProjectDetail(View):

            login_required = True
            template_name = 'project_detail.html'

            def response(self, request, project_id):
                self.context['project'] = get_object_or_404(Project, id=project_id)
                return self.context

    Typically, we would hook such defined views at ``urls.py`` module::

        from django.conf.urls.defaults import *

        urlpatterns = patterns('projector.views',
            (r'^projects/$', 'ProjectList'),
            (r'^projects/(?P<project_id>\d+)/$', 'ProjectDetail'),
        )

    Note that url resolvers pass all parameters to the given functions. Our
    subclasses of :view:`View` class are treated very similar to functions
    as they should return ``HttpResponse`` object after being called.
    """
    login_required = False
    template_name = 'base.html'

    def __new__(cls, request, *args, **kwargs):
        """
        Customized new instance static method.
        """
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
        method after ``response`` method is executed. By subclassing it is
        possible to change the order of method calls.
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

    def response(self, request, *args, **kwargs):
        """
        Should be overridden at subclass. It always requires
        ``django.http.HttpRequest`` instance to be passed as first positional
        argument.

        May return a ``dict`` or ``django.http.HttpResponse`` instance. If
        ``dict`` is returned it is treated as *context* and view would try
        to render it using ``self.template_name``.

        :returns: ``dict`` or ``django.http.HttpResponse`` instance
        """
        return self.context

