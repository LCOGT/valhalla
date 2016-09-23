from django import forms
from django.forms import ModelForm

from valhalla.sciapplications.models import ScienceApplication, Call


class BaseProposalAppForm(ModelForm):
    semester = forms.ModelChoiceField(
        queryset=Call.objects.all(),
        widget=forms.HiddenInput
    )


class ScienceProposalAppForm(BaseProposalAppForm):
    class Meta:
        model = ScienceApplication
        fields = [
            'title', 'pi', 'coi', 'budget_details', 'instruments',
            'abstract', 'moon', 'science_case', 'experimental_design',
            'experimental_design_file', 'related_programs', 'past_use',
            'publications', 'final'
        ]


class DDTProposalAppForm(BaseProposalAppForm):
    class Meta:
        model = ScienceApplication
        fields = [
            'title', 'pi', 'coi', 'budget_details', 'instruments',
            'science_justification', 'ddt_justification'
        ]


class KeyProjectAppForm(BaseProposalAppForm):
    class Meta:
        model = ScienceApplication
        fields = [
            'title', 'pi', 'coi', 'budget_details', 'instruments',
            'abstract', 'moon', 'related_programs', 'past_use', 'publications',
            'experimental_design', 'management', 'relevance', 'contribution',
            'attachment', 'final'
        ]
