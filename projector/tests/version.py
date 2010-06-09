import projector
from django.test import TestCase

class ProjectorVersionTests(TestCase):
    """
    Checks if ``__version__`` and ``VERSION`` attributes
    are set correctly in main module.
    """

    def test_version(self):
        self.assertTrue(isinstance(projector.__version__, str))
        self.assertTrue(isinstance(projector.VERSION, tuple))

        VERSION_LENGTH = len(projector.VERSION)
        self.assertTrue(3 <= VERSION_LENGTH and VERSION_LENGTH <= 5)

