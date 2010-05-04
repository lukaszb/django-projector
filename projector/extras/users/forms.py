from django import forms

from richtemplates.forms import RichSkinChoiceField, RichCodeStyleChoiceField
from projector.extras.users.models import UserProfile

class UserProfileForm(forms.ModelForm):
    skin = RichSkinChoiceField()
    code_style = RichCodeStyleChoiceField()

    class Meta:
        model = UserProfile
        exclude = ('user', 'activation_token')

