from django import forms
from django.utils.translation import ugettext as _

class BaseForkForm(forms.Form):
    """
    Base form class for all forms used to create *external* fork.
    """

    help_text = ''

    as_private = forms.BooleanField(initial=False, label=_('As private'),
        help_text=_('Forks project as your private project'), required=False)

    def fork(self, request):
        """
        Actions needed to fork the project.

        :param request: :py:class:`django.http.HttpRequest`` object is required
          at forking process
        """
        raise NotImplementedError("ForkForm requires ``fork`` method to "
            "implements logic required for the forking process")

    def get_url(self):
        """
        Should return url to be set as ``fork_url`` attribute of the
        ``Project`` model.
        """
        raise NotImplementedError("Must be implemented in order to let project "
            "instance know where it was forked from")

