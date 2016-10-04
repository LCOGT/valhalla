from django import forms
from django.forms import ModelForm
from django.utils import timezone
from django.forms.models import inlineformset_factory
from django.utils.translation import ugettext_lazy as _
from django.core.validators import validate_email

from valhalla.sciapplications.models import ScienceApplication, Call, TimeRequest


class MultiEmailField(forms.Field):
    def to_python(self, value):
        if not value:
            return []
        return value.replace(' ', '').split(',')

    def validate(self, value):
        super(MultiEmailField, self).validate(value)
        for email in value:
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
    coi = MultiEmailField(required=False)

    def clean(self):
        super().clean()
        all_filled = all(v for v in self.cleaned_data.values())
        if self.cleaned_data.get('status') == 'SUBMITTED' and not all_filled:
            raise forms.ValidationError(_('Please fill out all required fields'))


class ScienceProposalAppForm(BaseProposalAppForm):
    class Meta:
        model = ScienceApplication
        fields = [
            'call', 'status', 'title', 'pi', 'coi', 'budget_details', 'instruments',
            'abstract', 'moon', 'science_case', 'experimental_design',
            'experimental_design_file', 'related_programs', 'past_use',
            'publications'
        ]


class DDTProposalAppForm(BaseProposalAppForm):
    class Meta:
        model = ScienceApplication
        fields = [
            'call', 'status', 'title', 'pi', 'coi', 'budget_details', 'instruments',
            'science_justification', 'ddt_justification'
        ]


class KeyProjectAppForm(BaseProposalAppForm):
    class Meta:
        model = ScienceApplication
        fields = [
            'call', 'status', 'title', 'pi', 'coi', 'budget_details', 'instruments',
            'abstract', 'moon', 'science_case', 'related_programs', 'past_use', 'publications',
            'experimental_design', 'experimental_design_file', 'management', 'relevance',
            'contribution'
        ]


class TimeRequestForm(ModelForm):
    class Meta:
        model = TimeRequest
        fields = '__all__'


TimeRequestFormset = inlineformset_factory(
    ScienceApplication, TimeRequest, form=TimeRequestForm, extra=1
)
