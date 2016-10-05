from django import forms
from django.forms import ModelForm
from django.utils import timezone
from django.forms.models import inlineformset_factory
from django.utils.translation import ugettext as _
from django.core.validators import validate_email

from valhalla.sciapplications.models import ScienceApplication, Call, TimeRequest


def validate_multiemails(value):
    values = value.replace(' ', '').split(',')
    for email in values:
        validate_email(email)


class BaseProposalAppForm(ModelForm):
    call = forms.ModelChoiceField(
        queryset=Call.objects.filter(
            start__lt=timezone.now(),
            deadline__gte=timezone.now()
        ),
        widget=forms.HiddenInput
    )
    status = forms.CharField(widget=forms.HiddenInput, initial='DRAFT')
    coi = forms.CharField(validators=[validate_multiemails], required=False)

    def clean(self):
        super().clean()
        for field in self.Meta.required_fields:
            if not self.cleaned_data.get(field) and self.cleaned_data.get('status') == 'SUBMITTED':
                self.add_error(field, _('This field is required'))
        if self.errors:
            self.add_error(None, _('There was an error with your submission.'))

    def clean_pi(self):
        email = self.cleaned_data.get('pi')
        if email and email.strip() == self.instance.submitter.email:
            raise forms.ValidationError(_('Leave this field blank if you are the PI'))
        return email


class ScienceProposalAppForm(BaseProposalAppForm):
    class Meta:
        model = ScienceApplication
        fields = (
            'call', 'status', 'title', 'pi', 'coi', 'budget_details', 'instruments',
            'abstract', 'moon', 'science_case', 'experimental_design',
            'experimental_design_file', 'related_programs', 'past_use',
            'publications'
        )
        required_fields = set(fields) - set(('pi', 'coi', 'experimental_design_file'))


class DDTProposalAppForm(BaseProposalAppForm):
    class Meta:
        model = ScienceApplication
        fields = (
            'call', 'status', 'title', 'pi', 'coi', 'budget_details', 'instruments',
            'science_justification', 'ddt_justification'
        )
        required_fields = set(fields) - set(('pi', 'coi'))


class KeyProjectAppForm(BaseProposalAppForm):
    class Meta:
        model = ScienceApplication
        fields = (
            'call', 'status', 'title', 'pi', 'coi', 'budget_details', 'instruments',
            'abstract', 'moon', 'science_case', 'related_programs', 'past_use', 'publications',
            'experimental_design', 'experimental_design_file', 'management', 'relevance',
            'contribution'
        )
        required_fields = set(fields) - set(('pi', 'coi', 'experimental_design_file'))


class TimeRequestForm(ModelForm):
    class Meta:
        model = TimeRequest
        exclude = ('approved',)


TimeRequestFormset = inlineformset_factory(
    ScienceApplication, TimeRequest, form=TimeRequestForm, extra=1
)
