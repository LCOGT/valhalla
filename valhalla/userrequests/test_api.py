from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from valhalla.userrequests.models import UserRequest, Request
from valhalla.proposals.models import Proposal, Membership
from rest_framework.test import APITestCase

from mixer.backend.django import mixer


class TestUserGetRequestApi(APITestCase):
    def setUp(self):
        self.proposal = mixer.blend(Proposal)
        self.user = mixer.blend(User)
        self.other_user = mixer.blend(User)
        mixer.blend(Membership, user=self.user, proposal=self.proposal)

    def test_get_user_request_detail_unauthenticated(self):
        self.client.force_login(self.other_user)
        user_request = mixer.blend(UserRequest, submitter=self.user, proposal=self.proposal, group_id="testgroup")
        result = self.client.get(reverse('api:user_requests-detail', args=(user_request.id,)))
        self.assertEqual(result.status_code, 404)

    def test_get_user_request_detail_authenticated(self):
        user_request = mixer.blend(UserRequest, submitter=self.user, proposal=self.proposal, group_id="testgroup")
        self.client.force_login(self.user)
        result = self.client.get(reverse('api:user_requests-detail', args=(user_request.id,)))
        self.assertContains(result, user_request.group_id)

    def test_get_user_request_list_unauthenticated(self):
        self.client.force_login(self.other_user)
        mixer.blend(UserRequest, submitter=self.user, proposal=self.proposal, group_id="testgroup")
        result = self.client.get(reverse('api:user_requests-list'))
        self.assertEquals(result.status_code, 200)
        self.assertEquals(result.json(), [])

    def test_get_user_request_list_authenticated(self):
        user_request = mixer.blend(UserRequest, submitter=self.user, proposal=self.proposal, group_id="testgroup")
        self.client.force_login(self.user)
        result = self.client.get(reverse('api:user_requests-list'))
        self.assertContains(result, user_request.group_id)


class TestUserPostRequestApi(APITestCase):
    def setUp(self):
        self.proposal = mixer.blend(Proposal)
        self.user = mixer.blend(User)
        self.client.force_login(self.user)

        mixer.blend(Membership, user=self.user, proposal=self.proposal)
        self.generic_payload = {
            'proposal': self.proposal.id,
            'group_id': 'test group',
            'operator': 'AND',
            'ipp_value': 1.0,
            'requests': [{
                'target': {
                    'name': 'fake target',
                    'type': 'SIDEREAL',
                    'ra': 12.0,
                    'dec': 34.4,
                    'epoch': 2000,
                },
                'molecules': [{
                    'type': 'EXPOSE',
                    'instrument_name': '1M0SciCam',
                    'filter': 'air',
                    'exposure_time': 100,
                    'exposure_count': 1,
                    'bin_x': 1,
                    'bin_y': 1,
                }],
                'windows': [{
                    'start': '2016-09-29T21:12:18Z',
                    'end': '2016-10-29T21:12:19Z'
                }],
                'location': {
                    'telescope_class': '1m0',
                },
                'constraints': {
                    'max_airmass': 2.0,
                    'min_lunar_distance': 30.0,
                }
            }]
        }

    def test_post_userrequest_unauthenticated(self):
        self.other_user = mixer.blend(User)
        self.client.force_login(self.other_user)
        response = self.client.post(reverse('api:user_requests-list'), data=self.generic_payload)
        self.assertEqual(response.status_code, 400)

    def test_post_userrequest_authenticated(self):
        response = self.client.post(reverse('api:user_requests-list'), data=self.generic_payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['group_id'], self.generic_payload['group_id'])

    def test_post_userrequest_wrong_proposal(self):
        bad_data = self.generic_payload.copy()
        bad_data['proposal'] = 'DoesNotExist'
        response = self.client.post(reverse('api:user_requests-list'), data=bad_data)
        self.assertEqual(response.status_code, 400)

    def test_post_userrequest_missing_data(self):
        bad_data = self.generic_payload.copy()
        del bad_data['requests']
        response = self.client.post(reverse('api:user_requests-list'), data=bad_data)
        self.assertEqual(response.status_code, 400)

    def test_post_userrequest_empty_data(self):
        bad_data = self.generic_payload.copy()
        bad_data['requests'] = []
        response = self.client.post(reverse('api:user_requests-list'), data=bad_data)
        self.assertEqual(response.status_code, 400)


class TestGetRequestApi(APITestCase):
    def setUp(self):
        self.proposal = mixer.blend(Proposal)
        self.user = mixer.blend(User)
        mixer.blend(Membership, user=self.user, proposal=self.proposal)
        self.user_request = mixer.blend(UserRequest, submitter=self.user, proposal=self.proposal)

    def test_get_request_list_authenticated(self):
        request = mixer.blend(Request, user_request=self.user_request, observation_note='testobsnote')
        self.client.force_login(self.user)
        result = self.client.get(reverse('api:requests-list'))
        self.assertEquals(result.json()[0]['observation_note'], request.observation_note)

    def test_get_request_list_unauthenticated(self):
        mixer.blend(Request, user_request=self.user_request, observation_note='testobsnote')
        result = self.client.get(reverse('api:requests-list'))
        self.assertEquals(result.status_code, 403)

    def test_get_request_detail_authenticated(self):
        request = mixer.blend(Request, user_request=self.user_request, observation_note='testobsnote')
        self.client.force_login(self.user)
        result = self.client.get(reverse('api:requests-detail', args=(request.id,)))
        self.assertEquals(result.json()['observation_note'], request.observation_note)

    def test_get_request_detail_unauthenticated(self):
        request = mixer.blend(Request, user_request=self.user_request, observation_note='testobsnote')
        result = self.client.get(reverse('api:requests-detail', args=(request.id,)))
        self.assertEqual(result.status_code, 403)
