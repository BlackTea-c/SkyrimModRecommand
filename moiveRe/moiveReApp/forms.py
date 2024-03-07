# yourapp/forms.py
from django import forms
from django.contrib.auth.models import User  # 添加正确的导入语句,我还不确认是不是这个

class RatingForm(forms.Form):
    value = forms.IntegerField(min_value=1, max_value=5)
class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'password', 'email']

class UserLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)