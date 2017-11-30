from django.test import TestCase
from django.contrib.auth.models import User
from mixer.backend.django import mixer

from valhalla.sciapplications.models import ScienceApplication, Call, TimeRequest
from valhalla.proposals.models import Semester, Membership, ProposalInvite


class TestSciAppToProposal(TestCase):
    def setUp(self):
        self.semester = mixer.blend(Semester)
        self.user = mixer.blend(User)
        self.client.force_login(self.user)
        self.call = mixer.blend(
            Call, semester=self.semester,
            proposal_type=Call.SCI_PROPOSAL
        )

    def test_create_proposal_from_single_pi(self):
        app = mixer.blend(ScienceApplication, submitter=self.user, pi='', coi='')
        tr = mixer.blend(TimeRequest, approved=True, science_application=app)
        proposal = app.convert_to_proposal()
        self.assertEqual(app.proposal, proposal)
        self.assertEqual(self.user, proposal.membership_set.get(role=Membership.PI).user)
        self.assertEqual(proposal.timeallocation_set.first().std_allocation, tr.std_time)
        self.assertEqual(proposal.timeallocation_set.first().instrument_name, tr.instrument.code)
        self.assertFalse(ProposalInvite.objects.filter(proposal=proposal).exists())

    def test_create_proposal_with_supplied_noexistant_pi(self):
        app = mixer.blend(ScienceApplication, submitter=self.user, pi='frodo@example.com', coi='')
        tr = mixer.blend(TimeRequest, approved=True, science_application=app)
        proposal = app.convert_to_proposal()
        self.assertEqual(app.proposal, proposal)
        self.assertFalse(proposal.membership_set.all())
        self.assertEqual(proposal.timeallocation_set.first().std_allocation, tr.std_time)
        self.assertTrue(ProposalInvite.objects.filter(proposal=proposal, role=Membership.PI).exists())

    def test_create_proposal_with_supplied_existant_pi(self):
        user = mixer.blend(User)
        app = mixer.blend(ScienceApplication, submitter=self.user, pi=user.email, coi='')
        tr = mixer.blend(TimeRequest, approved=True, science_application=app)
        proposal = app.convert_to_proposal()
        self.assertEqual(app.proposal, proposal)
        self.assertEqual(user, proposal.membership_set.get(role=Membership.PI).user)
        self.assertEqual(proposal.timeallocation_set.first().std_allocation, tr.std_time)
        self.assertFalse(ProposalInvite.objects.filter(proposal=proposal).exists())

    def test_create_proposal_with_nonexistant_cois(self):
        cois = '1@lcogt.net, 2@lcogt.net,3@lcogt.net'
        app = mixer.blend(ScienceApplication, submitter=self.user, pi='', coi=cois)
        tr = mixer.blend(TimeRequest, approved=True, science_application=app)
        proposal = app.convert_to_proposal()
        self.assertEqual(app.proposal, proposal)
        self.assertEqual(self.user, proposal.membership_set.get(role=Membership.PI).user)
        self.assertEqual(proposal.timeallocation_set.first().std_allocation, tr.std_time)
        self.assertEqual(ProposalInvite.objects.filter(proposal=proposal).count(), 3)

    def test_create_proposal_with_existant_cois(self):
        cois = '1@lcogt.net, 2@lcogt.net,3@lcogt.net'
        coi1 = mixer.blend(User, email='1@lcogt.net')
        coi2 = mixer.blend(User, email='2@lcogt.net')
        app = mixer.blend(ScienceApplication, submitter=self.user, pi='', coi=cois)
        tr = mixer.blend(TimeRequest, approved=True, science_application=app)
        proposal = app.convert_to_proposal()
        self.assertEqual(app.proposal, proposal)
        self.assertEqual(self.user, proposal.membership_set.get(role=Membership.PI).user)
        self.assertEqual(proposal.timeallocation_set.first().std_allocation, tr.std_time)
        self.assertEqual(ProposalInvite.objects.filter(proposal=proposal).count(), 1)
        self.assertTrue(proposal.membership_set.filter(role=Membership.CI).filter(user__email=coi1.email).exists())
        self.assertTrue(proposal.membership_set.filter(role=Membership.CI).filter(user__email=coi2.email).exists())
