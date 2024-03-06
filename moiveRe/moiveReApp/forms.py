# yourapp/forms.py
from django import forms

class RatingForm(forms.Form):
    value = forms.IntegerField(min_value=1, max_value=5)
