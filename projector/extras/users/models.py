from django.db import models
from django.utils.translation import ugettext as _

from projector.utils import using_projector_profile

class UserProfile(models.Model):
    """
    Base user profile class for ``django-projector``.
    Would be abstract if ``AUTH_PROFILE_MODULE`` is not set or doesn't equal
    with ``projector.UserProfile``.
    """
    user = models.ForeignKey('auth.User', verbose_name=_('user'), unique=True)
    activation_token = models.CharField(_('activation_token'), max_length=32)
    skin = models.CharField(_('Color schema'), max_length=64)

    class Meta:
        app_label = 'projector'
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')
        abstract = not using_projector_profile()

    def __unicode__(self):
        return u"<%s's profile>" % self.user


