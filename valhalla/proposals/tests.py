from django.test import TestCase
from django.core import mail
from django.contrib.auth.models import User
from mixer.backend.django import mixer

from valhalla.proposals.models import ProposalInvite


class TestProposalInvitation(TestCase):
    def test_send_invitation(self):
        invitation = mixer.blend(ProposalInvite)
        invitation.send_invitation('test@example.com')
        self.assertIn(str(invitation.token), str(mail.outbox[0].message()))
        self.assertIn(invitation.proposal.code, str(mail.outbox[0].message()))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['test@example.com'])

    def test_accept(self):
        invitation = mixer.blend(ProposalInvite)
        user = mixer.blend(User)
        invitation.accept(user)
        self.assertIn(invitation.proposal, user.proposal_set.all())
