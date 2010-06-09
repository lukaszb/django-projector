from django import forms
from django.utils.translation import ugettext_lazy as _

def IntegerValidator(min, max):
    """
    Factory function, returns validator method processing integers.
    """
    def _validator(value):
        try:
            int(value)
            if value < min:
                raise forms.ValidationError(_("Minimum is %d" % min))
            elif value > max:
                raise forms.ValidationError(_("Maximum is %d" % max))
        except TypeError:
            raise forms.ValidationError(_("Must be a number"))
        return value
    return _validator


