from django.db import models
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

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

class UserId(models.Model):
    """
    This class would allow to identify users by some kind of id string. Created
    for repository browser - many scm's allow to use username/email combination
    and they may vary. User would be allowed to add such combinations in order
    to be identified by information given from changesets.
    If email is found within given ``raw_id``, user would need to activate this
    UserId - message would be send to the email found.
    """
    user = models.ForeignKey(User, verbose_name = _('user'))
    raw_id = models.CharField(_('Raw ID'), max_length=128, unique=True)
    is_active = models.BooleanField(_('is active'), default=False)
    activation_token = models.CharField(_('activation_token'), max_length=32,
        editable=False)

    def __unicode__(self):
        return self.raw_id

    def save(self, *args, **kwargs):
        if self.raw_id:
            user = get_user_from_string(self.raw_id)
            if user:
                raise ValidationError(_("User %s has been identified by this "
                    "value" % user))
        return super(UserId, self).save(*args, **kwargs)

def get_user_from_string(value):
    """
    Returns User instance if given text can be identified or None otherwise.
    First it tries to match with User.username or User.email, next would try
    to match with UserId.raw_id.
    """
    if not value:
        return None
    try:
        return User.objects.get(username=value)
    except User.DoesNotExist:
        pass
    try:
        return User.objects.get(email=value)
    except User.DoesNotExist:
        pass
    try:
        return UserId.objects.get(raw_id=value).user
    except UserId.DoesNotExist:
        pass
    return None

