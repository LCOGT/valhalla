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

    field_order = [
        'first_name', 'last_name', 'institution', 'title',
        'email', 'username', 'password1', 'password2', 'tos'
    ]

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
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


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

    def clean_email(self):
        email = self.cleaned_data['email']
        if email and User.objects.filter(email=email).exclude(pk=self.instance.id).exists():
            raise forms.ValidationError('User with this email already exists')
        return email


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['institution', 'title', 'notifications_enabled', 'simple_interface']
        help_texts = {
            'notifications_enabled': 'Recieve email notifications for every completed observation on all proposals.'
        }
