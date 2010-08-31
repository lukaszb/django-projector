"""
Tests here shouldn't be run with sqlite backend.
"""
from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse

from projector.tests.base import test_concurrently

class ThreadedProjectTest(TestCase):

    def test_list(self):

        url = reverse('projector_project_list')

        @test_concurrently(10)
        def toggle_test():
            client = Client()
            client.get(url)

        toggle_test()

