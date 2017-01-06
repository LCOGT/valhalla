from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils import timezone
from mixer.backend.django import mixer

from valhalla.proposals.models import Proposal, Membership
from valhalla.userrequests.models import UserRequest, Request, Molecule
from valhalla.common.test_telescope_states import TelescopeStatesFromFile
from valhalla.common.test_helpers import ConfigDBTestMixin


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


class TestRequestList(TestCase):
    def setUp(self):
        self.user = mixer.blend(User)
        self.proposal = mixer.blend(Proposal)
        mixer.blend(Membership, proposal=self.proposal, user=self.user)
        self.userrequest = mixer.blend(UserRequest, proposal=self.proposal, group_id=mixer.RANDOM)
        self.requests = mixer.cycle(10).blend(Request, user_request=self.userrequest)
        for request in self.requests:
            mixer.blend(Molecule, request=request, instrument_name='1M0-SCICAM-SBIG')
        self.client.force_login(self.user)

    def test_request_list(self):
        response = self.client.get(reverse('userrequests:list', kwargs={'ur': self.userrequest.id}))
        for request in self.requests:
            self.assertContains(response, request.id)


class TestTelescopeStates(TelescopeStatesFromFile):
    def setUp(self):
        super().setUp()
        self.user = mixer.blend(User)
        self.client.force_login(self.user)

    def test_date_format_1(self):
        response = self.client.get(reverse('telescope_states') + '?start=2016-10-1&end=2016-10-10')
        self.assertContains(response, "lsc")

    def test_date_format_2(self):
        response = self.client.get(reverse('telescope_availability') +
                                   '?start=2016-10-1T1:23:44&end=2016-10-10T22:22:2')
        self.assertContains(response, "lsc")

    def test_date_format_bad(self):
        response = self.client.get(reverse('telescope_states') +
                                   '?start=2016-10-1%201:3323:44&end=10-10T22:22:2')
        self.assertEqual(response.status_code, 400)
        self.assertIn("minute must be in 0..59", str(response.content))

    def test_no_date_specified(self):
        response = self.client.get(reverse('telescope_states'))
        self.assertContains(response, str(timezone.now().date()))


class TestInstrumentInformation(ConfigDBTestMixin, TestCase):
    def test_instrument_information(self):
        response = self.client.get(
            reverse('api:instrument_information', kwargs={'instrument_type': '1M0-SCICAM-SBIG'})
        )
        self.assertIn('air', response.json()['filters'])
        self.assertTrue(True)
