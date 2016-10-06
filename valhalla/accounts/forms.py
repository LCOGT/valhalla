from django import forms
from django.contrib.auth.models import User
from registration.forms import RegistrationFormTermsOfService, RegistrationFormUniqueEmail

from valhalla.accounts.models import Profile
from valhalla.proposals.models import ProposalInvite


class CustomRegistrationForm(RegistrationFormTermsOfService, RegistrationFormUniqueEmail):
    first_name = forms.CharField(max_length=200)
    last_name = forms.CharField(max_length=200)
    institution = forms.CharField(max_length=200)
    title = forms.CharField(max_length=200)
    ptoken = forms.CharField(max_length=64, widget=forms.HiddenInput, required=False)

    field_order = [
        'first_name', 'last_name', 'institution', 'title',
        'email', 'username', 'password1', 'password2', 'tos'
    ]

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'ptoken')
        help_texts = {
            'username': 'Will be present under the USERID fits header.'
        }

    def save(self, commit=True):
        new_user_instance = super().save(commit)
        Profile.objects.create(
            user=new_user_instance,
            title=self.cleaned_data['title'],
            institution=self.cleaned_data['institution']
        )
        for invite in ProposalInvite.objects.filter(email=new_user_instance.email):
            invite.accept(new_user_instance)

        return new_user_instance
