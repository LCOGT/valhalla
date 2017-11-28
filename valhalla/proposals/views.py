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
from django.contrib.auth.mixins import UserPassesTestMixin

from valhalla.sciapplications.models import Call
from valhalla.proposals.forms import ProposalNotificationForm
from valhalla.proposals.models import Proposal, Membership, ProposalNotification, Semester
from valhalla.proposals.filters import ProposalFilter


class ProposalDetailView(LoginRequiredMixin, DetailView):
    model = Proposal

    def get_queryset(self):
        if self.request.user.is_staff:
            return Proposal.objects.all()
        return self.request.user.proposal_set.all()

    def post(self, request, **kwargs):
        form = ProposalNotificationForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['notifications_enabled']:
                ProposalNotification.objects.get_or_create(user=request.user, proposal=self.get_object())
            else:
                ProposalNotification.objects.filter(user=request.user, proposal=self.get_object()).delete()
        messages.success(request, 'Preferences saved.')
        return HttpResponseRedirect(reverse('proposals:detail', kwargs={'pk': self.get_object().id}))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        enabled = ProposalNotification.objects.filter(user=self.request.user, proposal=self.get_object()).exists()
        context['notification_form'] = ProposalNotificationForm(initial={'notifications_enabled': enabled})
        return context


class ProposalListView(LoginRequiredMixin, FilterView):
    filterset_class = ProposalFilter
    template_name = 'proposals/proposal_list.html'
    model = Proposal

    def get_queryset(self):
        return self.request.user.proposal_set.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['calls'] = Call.open_calls()
        return context


class MembershipLimitView(LoginRequiredMixin, View):
    def post(self, request, **kwargs):
        membership = Membership.objects.get(pk=kwargs.get('pk'))
        if membership.proposal not in [m.proposal for m in request.user.membership_set.filter(role=Membership.PI)]:
            raise Http404
        membership.time_limit = request.POST['time_limit']
        membership.save()
        messages.success(request, 'Time limit for {0} {1} set to {2} seconds'.format(
            membership.user.first_name, membership.user.last_name, request.POST['time_limit']
        ))
        return HttpResponseRedirect(reverse('proposals:detail', kwargs={'pk': membership.proposal.id}))


class InviteCreateView(LoginRequiredMixin, View):
    def post(self, request, **kwargs):
        try:
            proposal = request.user.membership_set.get(proposal=kwargs.get('pk'), role=Membership.PI).proposal
        except Membership.DoesNotExist:
            raise Http404
        emails = request.POST['email'].replace(' ', '').strip(',').split(',')
        valid = True
        for email in emails:
            try:
                validate_email(email)
            except ValidationError:
                valid = False
                messages.error(request, _('Please enter a valid email address: {}'.format(email)))
        if valid:
            proposal.add_users(emails, Membership.CI)
            messages.success(request, _('Co Investigator(s) invited'))
        return HttpResponseRedirect(reverse('proposals:detail', kwargs={'pk': proposal.id}))


class MembershipDeleteView(LoginRequiredMixin, DeleteView):
    model = Membership

    def get_success_url(self):
        return reverse_lazy('proposals:detail', kwargs={'pk': self.get_object().proposal.id})

    def get_queryset(self):
        proposals = self.request.user.proposal_set.filter(membership__role=Membership.PI)
        return Membership.objects.filter(proposal__in=proposals)


class SemesterDetailView(UserPassesTestMixin, DetailView):
    model = Semester

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['semesters'] = Semester.objects.all().order_by('-start')
        return context
