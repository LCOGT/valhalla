from django.views import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.validators import validate_email
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse_lazy
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.contrib import messages
from django_filters.views import FilterView
from django.utils.translation import ugettext as _

from valhalla.proposals.models import Proposal, Membership
from valhalla.proposals.filters import ProposalFilter


class ProposalDetailView(LoginRequiredMixin, DetailView):
    model = Proposal

    def get_queryset(self):
        return self.request.user.proposal_set.all()


class ProposalListView(LoginRequiredMixin, FilterView):
    filterset_class = ProposalFilter
    template_name = 'proposals/proposal_list.html'
    model = Proposal

    def get_queryset(self):
        return self.request.user.proposal_set.all()


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


class MembershipDeleteView(LoginRequiredMixin, DeleteView):
    model = Membership

    def get_success_url(self):
        return reverse_lazy('proposals:detail', kwargs={'pk': self.get_object().proposal.id})

    def get_queryset(self):
        proposals = self.request.user.proposal_set.filter(membership__role=Membership.PI)
        return Membership.objects.filter(proposal__in=proposals)
