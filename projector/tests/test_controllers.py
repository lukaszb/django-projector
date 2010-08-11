from django.test import TestCase
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.models import AnonymousUser

from projector.core.controllers import View

class ViewTest(TestCase):

    def setUp(self):
        self.request = HttpRequest()
        self.request.user = AnonymousUser()

    def test_response(self):

        class AnyView(View):
            template_name = 'tests/dummy.html'

        response = AnyView(self.request)
        self.assertTrue(isinstance(response, HttpResponse))

    def test_dict_response(self):

        class DictView(View):
            template_name = 'tests/dummy.html'
            def response(self, request):
                return self.context

        response = DictView(self.request)
        self.assertTrue(isinstance(response, HttpResponse))

    def test_login_required(self):

        class LoginRequiredView(View):
            template_name = 'tests/dummy.html'
            login_required = True
            def response(self, request):
                return self.context

        self.request.user = AnonymousUser()
        response = LoginRequiredView(self.request)
        self.assertEqual(response.status_code, 302)

    def test_before(self):

        test = self

        class BeforeView(View):
            template_name = 'tests/dummy.html'
            def __before__(self):
                self.context['before'] = 'before'
            def response(self, request):
                test.assertEqual(self.context['before'], 'before')

        self = test
        # Assertion is called inside response method at the BeforeView
        BeforeView(self.request)

    def test_before_response(self):

        class BeforeResponseView(View):
            template_name = 'tests/dummy.html'
            def __before__(self):
                return HttpResponse(content='foobar', status=500)
            def response(self, request):
                return HttpResponse(status=200)

        response = BeforeResponseView(self.request)
        self.assertEqual(response.status_code, 500)

    def test_after(self):

        test = self

        class AfterView(View):
            template_name = 'tests/dummy.html'
            def __after__(self):
                self.context['after'] = 'after'
                if self._response.status_code == 200:
                    self._response.status_code = 501
            def response(self, request):
                test.assertFalse('after' in self.context)
                return self.context

        self = test
        # Assertion is called inside response method at AfterView
        AfterView(self.request)

    def test_after_response(self):

        class AfterResponseView(View):
            template_name = 'tests/dummy.html'
            def __after__(self):
                return HttpResponse(content='foobar', status=500)
            def response(self, request):
                return HttpResponse(status=200)

        response = AfterResponseView(self.request)
        self.assertEqual(response.status_code, 500)

    def test_before_after_mix(self):

        test = self

        class BeforeAndAfterView(View):
            template_name = 'tests/dummy.html'
            def __before__(self):
                self.context['before'] = 'before'
                self.context['mix'] = 'before'
            def __after__(self):
                self.context['after'] = 'after'
                self.context['mix'] = 'after'
            def response(self, request):
                test.assertEqual(self.context['before'], 'before')
                test.assertEqual(self.context['mix'], 'before')
                test.assertFalse('after' in self.context)
                return self.context

        self = test
        # Assertions are called inside response method at BeforeAndAfterView
        BeforeAndAfterView(self.request)

