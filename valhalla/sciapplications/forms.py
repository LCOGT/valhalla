from django import forms
from django.forms import ModelForm
from django.utils import timezone
from django.utils.translation import ugettext as _

from valhalla.sciapplications.models import ScienceApplication, Call


class BaseProposalAppForm(ModelForm):
    call = forms.ModelChoiceField(
        queryset=Call.objects.filter(
            start__lt=timezone.now(),
            deadline__gte=timezone.now()
        ),
        widget=forms.HiddenInput
    )
    status = forms.CharField(widget=forms.HiddenInput, initial='DRAFT')

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
            'publications', 'final'
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
            'abstract', 'moon', 'related_programs', 'past_use', 'publications',
            'experimental_design', 'management', 'relevance', 'contribution',
            'attachment', 'final'
        ]
