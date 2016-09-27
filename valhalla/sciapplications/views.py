from django.views.generic.edit import CreateView, UpdateView
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin

from valhalla.sciapplications.models import Call, ScienceApplication
from valhalla.sciapplications.forms import (ScienceProposalAppForm,
                                            DDTProposalAppForm,
                                            KeyProjectAppForm)

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
            semester=self.request.GET.get('semester')
        )
        return {'call': call}

    def form_valid(self, form):
        print('form valid')
        form.instance.submitter = self.request.user
        return super().form_valid(form)


class SciApplicationUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'sciapplications/create.html'
    success_url = '/apply/'
    model = ScienceApplication

    def get_form_class(self):
        return FORM_CLASSES[self.object.call.proposal_type]
