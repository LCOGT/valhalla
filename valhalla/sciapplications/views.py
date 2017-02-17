from django.utils.translation import ugettext as _
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from weasyprint import HTML
from PyPDF2 import PdfFileMerger
import io

from valhalla.sciapplications.models import Call, ScienceApplication
from valhalla.sciapplications.forms import (
    ScienceProposalAppForm, DDTProposalAppForm, KeyProjectAppForm, timerequest_formset
)

FORM_CLASSES = {
    'SCI': ScienceProposalAppForm,
    'DDT': DDTProposalAppForm,
    'KEY': KeyProjectAppForm,
    'NAOC': ScienceProposalAppForm,
}


class SciApplicationCreateView(LoginRequiredMixin, CreateView):
    template_name = 'sciapplications/create.html'
    model = ScienceApplication

    def get_form_class(self):
        try:
            return FORM_CLASSES[self.call.proposal_type]
        except KeyError:
            raise Http404

    def get_success_url(self):
        if self.object.status == ScienceApplication.DRAFT:
            messages.add_message(self.request, messages.SUCCESS, _('Application created'))
            return reverse('sciapplications:update', kwargs={'pk': self.object.id})
        else:
            messages.add_message(self.request, messages.SUCCESS, _('Application successfully submitted'))
            return reverse('sciapplications:index')

    def get_initial(self):
        return {'call': self.call}

    def get(self, request, *args, **kwargs):
        self.object = None
        self.call = get_object_or_404(Call, pk=kwargs['call'])
        form = self.get_form()
        timerequest_form = timerequest_formset()
        return self.render_to_response(
            self.get_context_data(form=form, timerequest_form=timerequest_form, call=self.call)
        )

    def post(self, request, *args, **kwargs):
        self.object = None
        self.call = get_object_or_404(Call, pk=kwargs['call'])
        form = self.get_form()
        form.instance.submitter = request.user
        timerequest_form = timerequest_formset(self.request.POST)
        if form.is_valid() and timerequest_form.is_valid():
            return self.forms_valid({'main': form, 'tr': timerequest_form})
        else:
            return self.forms_invalid({'main': form, 'tr': timerequest_form})

    def forms_valid(self, forms):
        self.object = forms['main'].save()
        forms['tr'].instance = self.object
        forms['tr'].save()
        return HttpResponseRedirect(self.get_success_url())

    def forms_invalid(self, forms):
        return self.render_to_response(
            self.get_context_data(form=forms['main'], timerequest_form=forms['tr'], call=self.call)
        )


class SciApplicationUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'sciapplications/create.html'

    def get_queryset(self):
        return ScienceApplication.objects.filter(submitter=self.request.user)

    def get_success_url(self):
        if self.object.status == ScienceApplication.DRAFT:
            messages.add_message(self.request, messages.SUCCESS, _('Application saved'))
            return reverse('sciapplications:update', kwargs={'pk': self.object.id})
        else:
            messages.add_message(self.request, messages.SUCCESS, _('Application successfully submitted'))
            return reverse('sciapplications:index')

    def get_form_class(self):
        return FORM_CLASSES[self.object.call.proposal_type]

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.status == ScienceApplication.DRAFT:
            raise Http404
        form = self.get_form()
        timerequest_form = timerequest_formset(instance=self.object)
        return self.render_to_response(
            self.get_context_data(form=form, timerequest_form=timerequest_form, call=self.object.call)
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        timerequest_form = timerequest_formset(self.request.POST, instance=self.object)
        if form.is_valid() and timerequest_form.is_valid():
            return self.forms_valid({'main': form, 'tr': timerequest_form})
        else:
            return self.forms_invalid({'main': form, 'tr': timerequest_form})

    def forms_valid(self, forms):
        self.object = forms['main'].save()
        forms['tr'].instance = self.object
        forms['tr'].save()
        return HttpResponseRedirect(self.get_success_url())

    def forms_invalid(self, forms):
        return self.render_to_response(
            self.get_context_data(form=forms['main'], timerequest_form=forms['tr'], call=self.object.call)
        )


class SciApplicationDetailView(LoginRequiredMixin, DetailView):
    model = ScienceApplication

    def get_queryset(self):
        if self.request.user.is_staff:
            return ScienceApplication.objects.all()
        else:
            return ScienceApplication.objects.filter(submitter=self.request.user)


class SciApplicationDeleteView(LoginRequiredMixin, DeleteView):
    model = ScienceApplication
    success_url = reverse_lazy('sciapplications:index')

    def get_queryset(self):
        return ScienceApplication.objects.filter(submitter=self.request.user, status=ScienceApplication.DRAFT)


class SciApplicationIndexView(LoginRequiredMixin, TemplateView):
    template_name = 'sciapplications/index.html'

    def get_context_data(self):
        calls = Call.objects.filter(opens__lte=timezone.now(), deadline__gte=timezone.now())
        draft_proposals = ScienceApplication.objects.filter(
            submitter=self.request.user, status=ScienceApplication.DRAFT
        )
        submitted_proposals = ScienceApplication.objects.filter(
            submitter=self.request.user).exclude(status=ScienceApplication.DRAFT)

        return {'calls': calls, 'draft_proposals': draft_proposals, 'submitted_proposals': submitted_proposals}


class SciApplicationPDFView(LoginRequiredMixin, DetailView):
    """Generate a pdf from the detailview, and append and file attachments to the end
    """
    model = ScienceApplication
    content_type = 'application/pdf'

    def get_queryset(self):
        if self.request.user.is_staff:
            return ScienceApplication.objects.all()
        else:
            return ScienceApplication.objects.filter(submitter=self.request.user)

    def render_to_response(self, context, **kwargs):
        context['pdf'] = True
        response = super().render_to_response(context, **kwargs)
        response.render()
        try:
            html = HTML(string=response.content)
            fileobj = io.BytesIO()
            html.write_pdf(fileobj)
            merger = PdfFileMerger()
            merger.append(fileobj)
            if self.object.science_case_file:
                merger.append(self.object.science_case_file.file)
            if self.object.experimental_design_file:
                merger.append(self.object.experimental_design_file.file)
            merger.write(response)
        except Exception as exc:
            error = 'There was an error generating your pdf. {}'
            messages.error(self.request, error.format(str(exc)))
            return HttpResponseRedirect(reverse('sciapplications:index'))
        return response
