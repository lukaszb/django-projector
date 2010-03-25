from django import forms

from richtemplates.forms import RichSkinChoiceField
from projector.extras.users.models import UserProfile

class UserProfileForm(forms.ModelForm):
    skin = RichSkinChoiceField()

    class Meta:
        model = UserProfile
        exclude = ('user', 'activation_token')

