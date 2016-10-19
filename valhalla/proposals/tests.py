from django.test import TestCase
from django.core import mail
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from mixer.backend.django import mixer

from valhalla.proposals.models import ProposalInvite, Proposal, Membership


class TestProposal(TestCase):
    def test_add_users(self):
        proposal = mixer.blend(Proposal)
        user = mixer.blend(User, email='email1@lcogt.net')
        emails = ['email1@lcogt.net', 'notexist@lcogt.net']
        proposal.add_users(emails, Membership.CI)
        self.assertIn(proposal, user.proposal_set.all())
        self.assertTrue(ProposalInvite.objects.filter(email='notexist@lcogt.net').exists())

    def test_no_dual_membership(self):
        proposal = mixer.blend(Proposal)
        user = mixer.blend(User)
        Membership.objects.create(user=user, proposal=proposal, role=Membership.PI)
        with self.assertRaises(IntegrityError):
            Membership.objects.create(user=user, proposal=proposal, role=Membership.CI)


class TestProposalInvitation(TestCase):
    def test_send_invitation(self):
        invitation = mixer.blend(ProposalInvite)
        invitation.send_invitation()
        self.assertIn(invitation.proposal.id, str(mail.outbox[0].message()))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [invitation.email])

    def test_accept(self):
        invitation = mixer.blend(ProposalInvite)
        user = mixer.blend(User)
        invitation.accept(user)
        self.assertIn(invitation.proposal, user.proposal_set.all())
