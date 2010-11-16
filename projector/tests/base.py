import sys

from django.conf import settings
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
                try:
                    import ipdb
                    ipdb.set_trace()
                except ImportError:
                    import pdb
                    pdb.set_trace()
            elif answer == 'c':
                sys.stdout.err.write(response.content)
            raise err

        return response

def get_homedir(project):
    """
    Returns homedir for single project.
    """
    import hashlib
    date = project.created_at.strftime('%Y%m%d%H%M%s')
    hex = hashlib.sha224(date).hexdigest()
    homedir = '-'.join(('test', date, str(project.id), hex))
    return homedir

def test_concurrently(times):
    """
    Add this decorator to small pieces of code that you want to test
    concurrently to make sure they don't raise exceptions when run at the
    same time.  E.g., some Django views that do a SELECT and then a subsequent
    INSERT might fail when the INSERT assumes that the data has not changed
    since the SELECT.

    Taken from http://www.caktusgroup.com/blog/2009/05/26/testing-django-views-for-concurrency-issues/
    """
    def test_concurrently_decorator(test_func):
        def wrapper(*args, **kwargs):
            if settings.DATABASE_ENGINE == 'sqlite3' or \
                ('default' in settings.DATABASES and
                 settings.DATABASES['default']['ENGINE'].split('.')[-1] ==
                 'sqlite3'):
                print "[WARNING] Concurrency tests are not applicable if "\
                      "sqlite3 is used as database engine"
                return
            exceptions = []
            import threading
            def call_test_func():
                try:
                    test_func(*args, **kwargs)
                except Exception, e:
                    exceptions.append(e)
                    raise
            threads = []
            for i in range(times):
                threads.append(threading.Thread(target=call_test_func))
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            if exceptions:
                raise Exception('test_concurrently intercepted %s exceptions: '
                '%s' % (len(exceptions), exceptions))
        return wrapper
    return test_concurrently_decorator

