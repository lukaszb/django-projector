from django.db import models
from django.utils.translation import ugettext as _

from projector.utils import using_projector_profile
from richtemplates.models import UserProfile as RichUserProfile

class UserProfile(RichUserProfile):
    """
    Base user profile class for ``django-projector``.
    Would be abstract if ``AUTH_PROFILE_MODULE`` is not set or doesn't equal
    with ``projector.UserProfile``.
    """
    activation_token = models.CharField(_('activation_token'), max_length=32,
        editable=False)

    class Meta:
        app_label = 'projector'
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')
        abstract = not using_projector_profile()

    def __unicode__(self):
        return u"<%s's profile>" % self.user


