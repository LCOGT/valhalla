from rest_framework.test import APITestCase
from mixer.backend.django import mixer
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User


from valhalla.proposals.models import Proposal, Membership


class TestProposalApiList(APITestCase):
    def setUp(self):
        self.user = mixer.blend(User)
        self.proposals = mixer.cycle(3).blend(Proposal)
        mixer.cycle(3).blend(Membership, user=self.user, proposal=(p for p in self.proposals))

    def test_no_auth(self):
        response = self.client.get(reverse('api:proposals-list'))
        self.assertEqual(response.status_code, 403)

    def test_user_can_view_proposals(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('api:proposals-list'))
        for p in self.proposals:
            self.assertContains(response, p.id)

    def test_user_cannot_view_other_proposals(self):
        other_user = mixer.blend(User)
        self.client.force_login(other_user)
        response = self.client.get(reverse('api:proposals-list'))
        self.assertEqual(response.json()['count'], 0)

    def test_staff_can_view_all_proposals(self):
        admin_user = mixer.blend(User, is_staff=True)
        self.client.force_login(admin_user)
        response = self.client.get(reverse('api:proposals-list'))
        for p in self.proposals:
            self.assertContains(response, p.id)


class TestProposalApiDetail(APITestCase):
    def setUp(self):
        self.user = mixer.blend(User)
        self.proposal = mixer.blend(Proposal)
        mixer.blend(Membership, user=self.user, proposal=self.proposal)

    def test_no_auth(self):
        response = self.client.get(reverse('api:proposals-detail', kwargs={'pk': self.proposal.id}))
        self.assertEqual(response.status_code, 403)

    def test_user_can_view_proposal(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('api:proposals-detail', kwargs={'pk': self.proposal.id}))
        self.assertContains(response, self.proposal.id)

    def test_user_cannot_view_other_proposal(self):
        other_user = mixer.blend(User)
        self.client.force_login(other_user)
        response = self.client.get(reverse('api:proposals-detail', kwargs={'pk': self.proposal.id}))
        self.assertEqual(response.status_code, 404)

    def test_staff_can_view_proposal(self):
        admin_user = mixer.blend(User, is_staff=True)
        self.client.force_login(admin_user)
        response = self.client.get(reverse('api:proposals-detail', kwargs={'pk': self.proposal.id}))
        self.assertContains(response, self.proposal.id)
