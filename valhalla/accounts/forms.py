from django import forms
from django.contrib.auth.models import User
from registration.forms import RegistrationFormTermsOfService, RegistrationFormUniqueEmail


class CustomRegistrationForm(RegistrationFormTermsOfService, RegistrationFormUniqueEmail):
    first_name = forms.CharField(max_length=200)
    last_name = forms.CharField(max_length=200)
    institution = forms.CharField(max_length=200)
    title = forms.CharField(max_length=200)
    ptoken = forms.CharField(max_length=64, widget=forms.HiddenInput, required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'ptoken')
        help_texts = {
            'username': 'Will be present under the USERID fits header.'
        }

    field_order = [
        'first_name', 'last_name', 'institution', 'title',
        'email', 'username', 'password1', 'password2', 'tos'
    ]
