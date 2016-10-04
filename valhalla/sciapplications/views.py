from django.views.generic.edit import CreateView, UpdateView
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from django.utils import timezone


from valhalla.sciapplications.models import Call, ScienceApplication
from valhalla.sciapplications.forms import (
    ScienceProposalAppForm, DDTProposalAppForm, KeyProjectAppForm, TimeRequestFormset
)

FORM_CLASSES = {
    'SCI': ScienceProposalAppForm,
    'DDT': DDTProposalAppForm,
    'KEY': KeyProjectAppForm
}


class SciApplicationCreateView(LoginRequiredMixin, CreateView):
    """Create a new science application

    Depending on the key kwarg (from url) we will return one of 3 classes defined in FORM_CLASSES
    The timerequest_from is an inline formset for a TimeRequest object.
    """
    template_name = 'sciapplications/create.html'
    success_url = '/apply/'
    model = ScienceApplication

    def get_form_class(self):
        try:
            return FORM_CLASSES[self.call.proposal_type]
        except KeyError:
            raise Http404

    def get_initial(self):
        return {'call': self.call}

    def get(self, request, *args, **kwargs):
        self.object = None
        self.call = get_object_or_404(Call, pk=kwargs['call'])
        form = self.get_form()
        timerequest_form = TimeRequestFormset()
        return self.render_to_response(
            self.get_context_data(form=form, timerequest_form=timerequest_form, call=self.call)
        )

    def post(self, request, *args, **kwargs):
        self.object = None
        self.call = get_object_or_404(Call, pk=kwargs['call'])
        form = self.get_form()
        timerequest_form = TimeRequestFormset(self.request.POST)
        if form.is_valid() and timerequest_form.is_valid():
            return self.forms_valid({'main': form, 'tr': timerequest_form})
        else:
            return self.forms_invalid({'main': form, 'tr': timerequest_form})

    def forms_valid(self, forms):
        forms['main'].instance.submitter = self.request.user
        self.object = forms['main'].save()
        forms['tr'].instance = self.object
        forms['tr'].save()
        return HttpResponseRedirect(self.get_success_url())

    def forms_invalid(self, forms):
        return self.render_to_response(
            self.get_context_data(form=forms['main'], timerequest_form=forms['tr'], call=self.call)
        )


class SciApplicationUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing science application

    Shares most logic with the CreateView, except that we have more information
    because we already have the ScienceApplication object
    """
    template_name = 'sciapplications/create.html'
    success_url = '/apply/'

    def get_queryset(self):
        return ScienceApplication.objects.filter(submitter=self.request.user)

    def get_form_class(self):
        return FORM_CLASSES[self.object.call.proposal_type]

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        timerequest_form = TimeRequestFormset(instance=self.object)
        return self.render_to_response(
            self.get_context_data(form=form, timerequest_form=timerequest_form, call=self.object.call)
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        timerequest_form = TimeRequestFormset(self.request.POST, instance=self.object)
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


class SciApplicationIndexView(TemplateView):
    template_name = 'sciapplications/index.html'

    def get_context_data(self):
        calls = Call.objects.filter(active=True, deadline__gte=timezone.now())
        return {'calls': calls}
