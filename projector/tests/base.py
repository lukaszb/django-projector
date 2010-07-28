import sys

from django.test import TestCase

class ProjectorTestCase(TestCase):

    def _get_response(self, url, data={}, method='GET', code=200, follow=False):
        """
        Test if response to given url/data/method returns with proper code.
        Returns response.
        """
        method = method.upper()
        if method == 'GET':
            opener = self.client.get
        elif method == 'POST':
            opener = self.client.post
        else:
            self.fail("Unsupported method %s" % method)

        response = opener(url, data, follow=follow)
        try:
            self.assertEqual(response.status_code, code)
        except AssertionError, err:
            answer = raw_input('\n'.join((
                "%s %s (data: %s) returned code %s but %s was expected"
                % (method, url, data, response.status_code, code),
                "AssertionError caught!",
                "USE: d (run debugger) | c (show content)",
                "[Enter to continue]",
            ))).lower()
            if answer == 'd':
                import pdb; pdb.set_trace()
            elif answer == 'c':
                sys.stdout.err.write(response.content)
            raise err

        return response

