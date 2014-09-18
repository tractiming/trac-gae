from django.contrib.auth.models import User
from django import forms

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    
    USER_CHOICES = (('1', 'Athlete'), ('2', 'Coach'))
    user_type = forms.ChoiceField(widget=forms.RadioSelect, choices=USER_CHOICES)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'user_type', 'password')


