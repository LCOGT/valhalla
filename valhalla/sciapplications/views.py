from django.views.generic.edit import CreateView, UpdateView
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect

from valhalla.sciapplications.models import Call, ScienceApplication
from valhalla.proposals.models import Semester
from valhalla.sciapplications.forms import (ScienceProposalAppForm,
                                            DDTProposalAppForm,
                                            KeyProjectAppForm,
                                            TimeRequestFormset)

FORM_CLASSES = {
    'SCI': ScienceProposalAppForm,
    'DDT': DDTProposalAppForm,
    'KEY': KeyProjectAppForm
}


class SciApplicationCreateView(LoginRequiredMixin, CreateView):
    template_name = 'sciapplications/create.html'
    success_url = '/apply/'
    model = ScienceApplication

    def get_form_class(self):
        proposal_type = self.request.GET.get('type')
        try:
            return FORM_CLASSES[proposal_type]
        except KeyError:
            raise Http404

    def get_initial(self):
        call = get_object_or_404(
            Call,
            proposal_type=self.request.GET.get('type'),
            semester=Semester.objects.get(code=self.request.GET.get('semester'))
        )
        return {'call': call}

    def get(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        timerequest_form = TimeRequestFormset()
        return self.render_to_response(
            self.get_context_data(form=form, timerequest_form=timerequest_form)
        )

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        timerequest_form = TimeRequestFormset(self.request.POST)
        if form.is_valid() and timerequest_form.is_valid():
            return self.form_valid(form, timerequest_form)
        else:
            return self.form_invalid(form, timerequest_form)

    def form_valid(self, form, timerequest_form):
        form.instance.submitter = self.request.user
        self.object = form.save()
        timerequest_form.instance = self.object
        timerequest_form.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, timerequest_form):
        return self.render_to_response(
            self.get_context_data(form=form, timerequest_form=timerequest_form)
        )


class SciApplicationUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'sciapplications/create.html'
    success_url = '/apply/'
    model = ScienceApplication

    def get_form_class(self):
        return FORM_CLASSES[self.object.call.proposal_type]

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        timerequest_form = TimeRequestFormset(instance=self.object)
        return self.render_to_response(
            self.get_context_data(form=form, timerequest_form=timerequest_form)
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        timerequest_form = TimeRequestFormset(self.request.POST, instance=self.object)
        if form.is_valid() and timerequest_form.is_valid():
            return self.form_valid(form, timerequest_form)
        else:
            return self.form_invalid(form, timerequest_form)

    def form_valid(self, form, timerequest_form):
        self.object = form.save()
        timerequest_form.instance = self.object
        timerequest_form.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, timerequest_form):
        return self.render_to_response(
            self.get_context_data(form=form, timerequest_form=timerequest_form)
        )
