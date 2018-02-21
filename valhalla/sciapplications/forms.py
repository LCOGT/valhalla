from django import forms
from django.forms import ModelForm
from django.forms.models import inlineformset_factory
from django.utils.translation import ugettext as _
import os

from valhalla.sciapplications.models import ScienceApplication, Call, TimeRequest, CoInvestigator


def validate_pdf_file(value):
    extension = os.path.splitext(value.name)[1]
    if extension not in ['.pdf', '.PDF']:
        raise forms.ValidationError(_('We can only accept PDF files.'))


class BaseProposalAppForm(ModelForm):
    call = forms.ModelChoiceField(
        queryset=Call.objects.all(),
        widget=forms.HiddenInput
    )
    status = forms.CharField(widget=forms.HiddenInput, initial='DRAFT')
    pdf = forms.FileField(validators=[validate_pdf_file], required=False)

    def clean(self):
        super().clean()
        if self.cleaned_data.get('pi'):
            self.Meta.required_fields.update(['pi_first_name', 'pi_last_name', 'pi_institution'])
        for field in self.Meta.required_fields:
            if not self.cleaned_data.get(field) and self.cleaned_data.get('status') == 'SUBMITTED':
                self.add_error(field, _('{}: This field is required'.format(self.fields[field].label)))
        if self.errors:
            self.add_error(None, _('There was an error with your submission.'))

    def clean_pi(self):
        email = self.cleaned_data.get('pi')
        if email and email.strip() == self.instance.submitter.email:
            raise forms.ValidationError(_('Leave these fields blank if you are the PI'))
        return email


class ScienceProposalAppForm(BaseProposalAppForm):
    class Meta:
        model = ScienceApplication
        fields = (
            'call', 'status', 'title', 'pi', 'pi_first_name', 'pi_last_name', 'pi_institution',
            'abstract', 'moon', 'pdf'
        )
        required_fields = set(fields) - set((
            'pi', 'pi_first_name', 'pi_last_name', 'pi_institution'
        ))


class DDTProposalAppForm(BaseProposalAppForm):
    class Meta:
        model = ScienceApplication
        fields = (
            'call', 'status', 'title', 'pi', 'pi_first_name', 'pi_last_name', 'pi_institution',
            'moon', 'pdf',
        )
        required_fields = set(fields) - set((
            'pi', 'pi_first_name', 'pi_last_name', 'pi_institution'
        ))


class KeyProjectAppForm(BaseProposalAppForm):
    class Meta:
        model = ScienceApplication
        fields = (
            'call', 'status', 'title', 'pi', 'pi_first_name', 'pi_last_name', 'pi_institution',
            'abstract', 'moon', 'pdf'
        )
        required_fields = set(fields) - set((
            'pi', 'pi_first_name', 'pi_last_name', 'pi_institution',
        ))


class TimeRequestForm(ModelForm):
    class Meta:
        model = TimeRequest
        exclude = ('approved',)


timerequest_formset = inlineformset_factory(
    ScienceApplication, TimeRequest, form=TimeRequestForm, extra=1
)


class CIForm(ModelForm):
    class Meta:
        model = CoInvestigator
        fields = '__all__'


ci_formset = inlineformset_factory(
    ScienceApplication, CoInvestigator, form=CIForm, extra=1
)
