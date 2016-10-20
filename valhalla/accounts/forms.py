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
    institution = forms.CharField(max_length=200)
    title = forms.CharField(max_length=200)
    notifications_enabled = forms.BooleanField()

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'username', 'email',
            'institution', 'title', 'notifications_enabled',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for k in self.fields:
            self.fields[k].required = True
        self.fields['institution'].initial = self.instance.profile.institution
        self.fields['title'].initial = self.instance.profile.title
        self.fields['notifications_enabled'].initial = self.instance.profile.notifications_enabled

    def clean_email(self):
        if User.objects.filter(email=self.cleaned_data['email']).exists():
            raise forms.ValidationError('User with this email already exists.')
        return self.cleaned_data['email']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.instance.profile.institution = self.cleaned_data.get('institution')
        self.instance.profile.last_name = self.cleaned_data.get('title')
        self.instance.profile.username = self.cleaned_data.get('notifications_enabled')
        self.instance.profile.save()
