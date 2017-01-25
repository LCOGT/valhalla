from django.views import View
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.validators import validate_email
from django.http import Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.utils.translation import ugettext as _

from valhalla.proposals.models import Proposal, Membership


class ProposalDetailView(LoginRequiredMixin, DetailView):
    model = Proposal

    def get_queryset(self):
        return self.request.user.proposal_set.all()


class ProposalListView(LoginRequiredMixin, ListView):
    model = Proposal

    def get_queryset(self):
        return self.request.user.proposal_set.filter(active=True)


class InviteCreateView(LoginRequiredMixin, View):
    def post(self, request, **kwargs):
        try:
            proposal = request.user.membership_set.get(proposal=kwargs.get('pk'), role=Membership.PI).proposal
        except Membership.DoesNotExist:
            raise Http404
        email = request.POST['email']
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, _('Please enter a valid email address'))
        else:
            proposal.add_users([email], Membership.CI)
            messages.success(request, _('Co Investigator invited'))
        return HttpResponseRedirect(reverse('proposals:detail', kwargs={'pk': proposal.id}))
