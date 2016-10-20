from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from mixer.backend.django import mixer

from valhalla.proposals.models import Proposal, Membership
from valhalla.userrequests.models import UserRequest, Request


class UserRequestList(TestCase):
    def setUp(self):
        self.user = mixer.blend(User)
        self.proposals = mixer.cycle(3).blend(Proposal)
        for proposal in self.proposals:
            mixer.blend(Membership, proposal=proposal, user=self.user)
        self.userrequests = mixer.cycle(3).blend(
            UserRequest,
            proposal=(p for p in self.proposals),
            group_id=mixer.RANDOM
        )
        self.requests = mixer.cycle(3).blend(
            Request,
            user_request=(ur for ur in self.userrequests),
        )
        self.client.force_login(self.user)

    def test_userrequest_list(self):
        response = self.client.get(reverse('index'))
        for ur in self.userrequests:
            self.assertContains(response, ur.group_id)
            for request in ur.request_set.all():
                self.assertContains(response, request.id)

    def test_userrequest_no_auth(self):
        self.client.logout()
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'In order to request observations, you must first')

    def test_no_other_requests(self):
        proposal = mixer.blend(Proposal)
        other_ur = mixer.blend(UserRequest, proposal=proposal, group_id=mixer.RANDOM)
        response = self.client.get(reverse('index'))
        self.assertNotContains(response, other_ur.group_id)

    def test_filtering(self):
        response = self.client.get(
            reverse('index') + '?title={}'.format(self.userrequests[0].group_id)
        )
        self.assertContains(response, self.userrequests[0].request_set.all()[0].id)
        self.assertNotContains(response, self.userrequests[1].group_id)
        self.assertNotContains(response, self.userrequests[2].group_id)
