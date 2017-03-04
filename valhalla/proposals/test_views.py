from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from mixer.backend.django import mixer

from valhalla.proposals.models import Membership, Proposal, ProposalInvite, ProposalNotification
from valhalla.proposals.models import Semester, TimeAllocation


class TestProposalDetail(TestCase):
    def setUp(self):
        self.proposal = mixer.blend(Proposal)
        self.pi_user = mixer.blend(User)
        self.ci_user = mixer.blend(User)
        Membership.objects.create(user=self.pi_user, proposal=self.proposal, role=Membership.PI)
        Membership.objects.create(user=self.ci_user, proposal=self.proposal, role=Membership.CI)

    def test_proposal_detail_as_pi(self):
        self.client.force_login(self.pi_user)
        response = self.client.get(reverse('proposals:detail', kwargs={'pk': self.proposal.id}))
        self.assertContains(response, self.proposal.id)

    def test_proposal_detail_as_ci(self):
        self.client.force_login(self.ci_user)
        response = self.client.get(reverse('proposals:detail', kwargs={'pk': self.proposal.id}))
        self.assertContains(response, self.proposal.id)
        self.assertNotContains(response, 'Pending Invitations')

    def test_show_pending_invites(self):
        invite = mixer.blend(ProposalInvite, used=None, proposal=self.proposal)
        self.client.force_login(self.pi_user)
        response = self.client.get(reverse('proposals:detail', kwargs={'pk': self.proposal.id}))
        self.assertContains(response, invite.email)


class TestProposalInvite(TestCase):
    def setUp(self):
        self.proposal = mixer.blend(Proposal)
        self.pi_user = mixer.blend(User)
        self.ci_user = mixer.blend(User)
        Membership.objects.create(user=self.pi_user, proposal=self.proposal, role=Membership.PI)
        Membership.objects.create(user=self.ci_user, proposal=self.proposal, role=Membership.CI)

    def test_invite(self):
        self.client.force_login(self.pi_user)
        response = self.client.post(
            reverse('proposals:invite', kwargs={'pk': self.proposal.id}),
            data={'email': 'rick@getschwifty.com'},
            follow=True
        )
        self.assertTrue(ProposalInvite.objects.filter(email='rick@getschwifty.com', proposal=self.proposal).exists())
        self.assertEqual(response.status_code, 200)

    def test_multiple_invite(self):
        self.client.force_login(self.pi_user)
        response = self.client.post(
            reverse('proposals:invite', kwargs={'pk': self.proposal.id}),
            data={'email': 'rick@getschwifty.com, morty@globbitygook.com, '},
            follow=True
        )
        self.assertTrue(ProposalInvite.objects.filter(email='rick@getschwifty.com', proposal=self.proposal).exists())
        self.assertTrue(ProposalInvite.objects.filter(email='morty@globbitygook.com', proposal=self.proposal).exists())
        self.assertEqual(response.status_code, 200)

    def test_invite_get(self):
        self.client.force_login(self.pi_user)
        response = self.client.get(reverse('proposals:invite', kwargs={'pk': self.proposal.id}))
        self.assertEqual(response.status_code, 405)

    def test_cannot_invite_to_other_proposal(self):
        self.client.force_login(mixer.blend(User))
        response = self.client.post(
            reverse('proposals:invite', kwargs={'pk': self.proposal.id}),
            data={'email': 'nefarious@evil.com'},
            follow=True
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(ProposalInvite.objects.filter(email='nefarious@evil.com', proposal=self.proposal).exists())

    def test_ci_cannot_invite(self):
        self.client.force_login(self.ci_user)
        response = self.client.post(
            reverse('proposals:invite', kwargs={'pk': self.proposal.id}),
            data={'email': 'nefarious@evil.com'},
            follow=True
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(ProposalInvite.objects.filter(email='nefarious@evil.com', proposal=self.proposal).exists())

    def test_validate_email(self):
        self.client.force_login(self.pi_user)
        response = self.client.post(
            reverse('proposals:invite', kwargs={'pk': self.proposal.id}),
            data={'email': 'notanemailaddress'},
            follow=True
        )
        self.assertFalse(ProposalInvite.objects.filter(email='notanemailaddress', proposal=self.proposal).exists())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter a valid email address')


class TestProposalList(TestCase):
    def setUp(self):
        self.user = mixer.blend(User)
        self.proposals = mixer.cycle(5).blend(Proposal)
        for proposal in self.proposals:
            mixer.blend(Membership, user=self.user, proposal=proposal)

    def test_no_proposals(self):
        user = mixer.blend(User)
        self.client.force_login(user)
        response = self.client.get(reverse('proposals:list'))
        self.assertContains(response, 'You are not a member of any proposals')
        self.assertNotContains(response, 'Admin only')

    def test_proposals_show_in_list(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('proposals:list'))
        for proposal in self.proposals:
            self.assertContains(response, proposal.id)

    def test_admin_link(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_login(self.user)
        response = self.client.get(reverse('proposals:list'))
        self.assertContains(response, 'Admin only')


class TestMembershipDelete(TestCase):
    def setUp(self):
        self.pi_user = mixer.blend(User)
        self.ci_user = mixer.blend(User)
        self.proposal = mixer.blend(Proposal)
        mixer.blend(Membership, user=self.pi_user, role=Membership.PI, proposal=self.proposal)
        self.cim = mixer.blend(Membership, user=self.ci_user, role=Membership.CI, proposal=self.proposal)

    def test_pi_can_remove_ci(self):
        self.client.force_login(self.pi_user)

        self.assertEqual(self.proposal.membership_set.count(), 2)
        response = self.client.post(
            reverse('proposals:membership-delete', kwargs={'pk': self.cim.id}),
            data={'submit': 'Confirm'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.proposal.membership_set.count(), 1)

    def test_ci_cannot_remove_ci(self):
        other_user = mixer.blend(User)
        other_cim = mixer.blend(Membership, user=other_user, proposal=self.proposal)

        self.client.force_login(self.ci_user)
        self.assertEqual(self.proposal.membership_set.count(), 3)
        response = self.client.post(
            reverse('proposals:membership-delete', kwargs={'pk': other_cim.id}),
            data={'submit': 'Confirm'},
            follow=True
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.proposal.membership_set.count(), 3)

    def test_pi_cannot_remove_ci_other_proposal(self):
        other_proposal = mixer.blend(Proposal)
        other_membership = mixer.blend(Membership, user=self.ci_user, proposal=other_proposal)

        self.client.force_login(self.pi_user)
        self.assertEqual(other_proposal.membership_set.count(), 1)
        response = self.client.post(
            reverse('proposals:membership-delete', kwargs={'pk': other_membership.id}),
            data={'submit': 'Confirm'},
            follow=True
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(other_proposal.membership_set.count(), 1)


class TestNotificationsEnabled(TestCase):
    def setUp(self):
        self.user = mixer.blend(User)
        self.proposal = mixer.blend(Proposal)
        mixer.blend(Membership, user=self.user, proposal=self.proposal)
        self.client.force_login(self.user)

    def test_user_can_enable_notifications(self):
        self.client.post(
            reverse('proposals:detail', kwargs={'pk': self.proposal.id}),
            data={'notifications_enabled': True},
        )
        self.assertEqual(self.user.proposalnotification_set.count(), 1)

    def test_user_can_disable_notifications(self):
        ProposalNotification.objects.create(user=self.user, proposal=self.proposal)
        self.client.post(
            reverse('proposals:detail', kwargs={'pk': self.proposal.id}),
            data={'notifications_enabled': False},
        )
        self.assertEqual(self.user.proposalnotification_set.count(), 0)


class TestSemesterDetail(TestCase):
    def setUp(self):
        self.user = mixer.blend(User, is_staff=True)
        self.proposal = mixer.blend(Proposal)
        self.semester = mixer.blend(Semester)
        self.ta = mixer.blend(TimeAllocation, semester=self.semester, proposal=self.proposal)

    def test_proposal_table(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse('proposals:semester-detail', kwargs={'pk': self.semester.id})
        )
        self.assertContains(response, self.proposal.id)

    def test_proposal_table_not_staff(self):
        user = mixer.blend(User)
        self.client.force_login(user)
        response = self.client.get(
            reverse('proposals:semester-detail', kwargs={'pk': self.semester.id})
        )
        self.assertEqual(response.status_code, 302)
