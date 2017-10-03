from django.test import TestCase
from django.core import mail
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.conf import settings
from django.utils import timezone
from mixer.backend.django import mixer
from unittest.mock import patch
from requests import HTTPError
import responses
import datetime

from valhalla.proposals.models import ProposalInvite, Proposal, Membership, ProposalNotification, TimeAllocation, Semester
from valhalla.userrequests.models import UserRequest
from valhalla.accounts.models import Profile
from valhalla.proposals.accounting import query_pond
from valhalla.proposals.tasks import run_accounting


class TestProposal(TestCase):
    def test_add_existing_user(self):
        proposal = mixer.blend(Proposal)
        user = mixer.blend(User, email='email1@lcogt.net')
        emails = ['email1@lcogt.net']
        proposal.add_users(emails, Membership.CI)
        self.assertIn(proposal, user.proposal_set.all())
        self.assertIn(proposal.title, str(mail.outbox[0].message()))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [user.email])

    def test_add_nonexisting_user(self):
        proposal = mixer.blend(Proposal)
        emails = ['email1@lcogt.net']
        proposal.add_users(emails, Membership.CI)
        self.assertFalse(proposal.users.count())
        self.assertTrue(ProposalInvite.objects.filter(email='email1@lcogt.net').exists())

    def test_add_nonexisting_user_twice(self):
        proposal = mixer.blend(Proposal)
        proposal_invite = mixer.blend(ProposalInvite, proposal=proposal, role=Membership.CI)
        proposal.add_users([proposal_invite.email], Membership.CI)
        self.assertEqual(ProposalInvite.objects.filter(email=proposal_invite.email).count(), 1)

    def test_no_dual_membership(self):
        proposal = mixer.blend(Proposal)
        user = mixer.blend(User)
        Membership.objects.create(user=user, proposal=proposal, role=Membership.PI)
        with self.assertRaises(IntegrityError):
            Membership.objects.create(user=user, proposal=proposal, role=Membership.CI)

    def test_user_already_member(self):
        proposal = mixer.blend(Proposal)
        user = mixer.blend(User)
        mixer.blend(Membership, proposal=proposal, user=user, role=Membership.CI)
        proposal.add_users([user.email], Membership.CI)
        self.assertIn(proposal, user.proposal_set.all())
        self.assertEqual(len(mail.outbox), 0)


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


class TestProposalNotifications(TestCase):
    def setUp(self):
        self.proposal = mixer.blend(Proposal)
        self.user = mixer.blend(User)
        mixer.blend(Membership, user=self.user, proposal=self.proposal)
        self.userrequest = mixer.blend(UserRequest, proposal=self.proposal, state='PENDING')

    def test_all_proposal_notification(self):
        mixer.blend(Profile, user=self.user, notifications_enabled=True)
        self.userrequest.state = 'COMPLETED'
        self.userrequest.save()
        self.assertIn(self.userrequest.group_id, str(mail.outbox[0].message()))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])

    def test_single_proposal_notification(self):
        mixer.blend(Profile, user=self.user, notifications_enabled=False)
        mixer.blend(ProposalNotification, user=self.user, proposal=self.proposal)
        self.userrequest.state = 'COMPLETED'
        self.userrequest.save()
        self.assertIn(self.userrequest.group_id, str(mail.outbox[0].message()))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])

    def test_user_loves_notifications(self):
        mixer.blend(Profile, user=self.user, notifications_enabled=True)
        mixer.blend(ProposalNotification, user=self.user, proposal=self.proposal)
        self.userrequest.state = 'COMPLETED'
        self.userrequest.save()
        self.assertIn(self.userrequest.group_id, str(mail.outbox[0].message()))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])

    def test_notifications_only_authored(self):
        mixer.blend(Profile, user=self.user, notifications_enabled=True, notifications_on_authored_only=True)
        self.userrequest.submitter = self.user
        self.userrequest.state = 'COMPLETED'
        self.userrequest.save()
        self.assertIn(self.userrequest.group_id, str(mail.outbox[0].message()))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])

    def test_no_notifications_only_authored(self):
        mixer.blend(Profile, user=self.user, notifications_enabled=True, notifications_on_authored_only=True)
        self.userrequest.author = mixer.blend(User)
        self.userrequest.state = 'COMPLETED'
        self.userrequest.save()
        self.assertEqual(len(mail.outbox), 0)

    def test_no_notifications(self):
        self.userrequest.state = 'COMPLETED'
        self.userrequest.save()
        self.assertEqual(len(mail.outbox), 0)


class TestAccounting(TestCase):
    @patch('valhalla.proposals.accounting.query_pond', return_value=1)
    def test_run_accounting(self, qa_mock):
        semester = mixer.blend(
            Semester, start=datetime.datetime(2017, 1, 1, tzinfo=timezone.utc), end=datetime.datetime(2017, 4, 30, tzinfo=timezone.utc))
        talloc = mixer.blend(
            TimeAllocation, semester=semester, std_allocation=10, too_allocation=10, std_time_used=0, too_time_used=0
        )
        run_accounting([semester])
        talloc.refresh_from_db()
        self.assertEqual(talloc.std_time_used, 1)
        self.assertEqual(talloc.too_time_used, 1)


class TestDefaultIPP(TestCase):
    def setUp(self):
        self.proposal = mixer.blend(Proposal)
        self.semester = mixer.blend(Semester)

    def test_default_ipp_time_is_set(self):
        ta = TimeAllocation(semester=self.semester, proposal=self.proposal, std_allocation=100)
        ta.save()
        self.assertEqual(ta.ipp_limit, 10)
        self.assertEqual(ta.ipp_time_available, 5)

    def test_default_ipp_time_is_not_set(self):
        ta = TimeAllocation(
            semester=self.semester, proposal=self.proposal, std_allocation=100, ipp_limit=99, ipp_time_available=42
        )
        ta.save()
        self.assertEqual(ta.ipp_limit, 99)
        self.assertEqual(ta.ipp_time_available, 42)

    def test_default_ipp_set_only_on_creation(self):
        ta = TimeAllocation(semester=self.semester, proposal=self.proposal, std_allocation=100)
        ta.save()
        ta.ipp_time_available = 0
        ta.save()
        self.assertEqual(ta.ipp_time_available, 0)
