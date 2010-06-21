from django.test import TestCase
from django.http import HttpRequest, HttpResponse

from projector.core.controllers import View

class ViewTest(TestCase):

    def setUp(self):
        self.request = HttpRequest()

    def test_response(self):

        class AnyView(View):
            template_name = 'tests/base.html'

        response = AnyView(self.request)
        self.assertTrue(isinstance(response, HttpResponse))

    def test_dict_response(self):

        class DictView(View):
            template_name = 'tests/base.html'
            def response(self, request):
                return {}

        response = DictView(self.request)
        self.assertTrue(isinstance(response, HttpResponse))


