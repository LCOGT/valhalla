from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from valhalla.userrequests.models import UserRequest, Request
from valhalla.proposals.models import Proposal, Membership
from valhalla.common.configdb_utils import get_configdb_data
from rest_framework.test import APITestCase

from mixer.backend.django import mixer
from mock import patch, MagicMock


class TestUserGetRequestApi(APITestCase):
    def setUp(self):
        self.proposal = mixer.blend(Proposal)
        self.user = mixer.blend(User, is_staff=False, is_superuser=False)
        self.other_user = mixer.blend(User, is_staff=False, is_superuser=False)
        mixer.blend(Membership, user=self.user, proposal=self.proposal)
        self.staff_user = mixer.blend(User, is_staff=True)

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

    def test_get_user_request_list_staff(self):
        user_request = mixer.blend(UserRequest, submitter=self.user, proposal=self.proposal, group_id="testgroup2")
        self.client.force_login(self.staff_user)
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
                    'dec': 34.4,
                    'ra': 20,
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

    def test_post_userrequest_no_molecules(self):
        bad_data = self.generic_payload.copy()
        bad_data['requests'][0]['molecules'] = []
        response = self.client.post(reverse('api:user_requests-list'), data=bad_data)
        self.assertEqual(response.status_code, 400)

    def test_post_userrequest_empty_data(self):
        bad_data = self.generic_payload.copy()
        bad_data['requests'] = []
        response = self.client.post(reverse('api:user_requests-list'), data=bad_data)
        self.assertEqual(response.status_code, 400)

    def test_post_userrequest_bad_ipp(self):
        bad_data = self.generic_payload.copy()
        bad_data['ipp_value'] = 0.0
        response = self.client.post(reverse('api:user_requests-list'), data=bad_data)
        self.assertEqual(response.status_code, 400)

    def test_post_userrequest_default_acquire_mode(self):
        bad_data = self.generic_payload.copy()
        # verify default acquire mode is 'optional' for non-floyds
        response = self.client.post(reverse('api:user_requests-list'), data=bad_data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['requests'][0]['target']['acquire_mode'], 'OPTIONAL')

        # check that default acquire mode is 'on' for floyds
        bad_data['requests'][0]['molecules'][0]['instrument_name'] = '2M0-FLOYDS-SCICAM'
        response = self.client.post(reverse('api:user_requests-list'), data=bad_data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['requests'][0]['target']['acquire_mode'], 'ON')


class TestWindowApi(APITestCase):
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
                    'dec': 34.4,
                    'ra': 20,
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

    def test_post_userrequest_window_end_before_start(self):
        bad_data = self.generic_payload.copy()
        bad_data['requests'][0]['windows'][0]['end'] = '2016-09-28T21:12:18Z'
        response = self.client.post(reverse('api:user_requests-list'), data=bad_data)
        self.assertEqual(response.status_code, 400)


class TestSiderealTarget(APITestCase):
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
                    'dec': 34.4,
                    'ra': 20,
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

    def test_post_userrequest_no_ra(self):
        bad_data = self.generic_payload.copy()
        del bad_data['requests'][0]['target']['ra']
        response = self.client.post(reverse('api:user_requests-list'), data=bad_data)
        self.assertEqual(response.status_code, 400)

    def test_post_userrequest_extra_ns_field(self):
        bad_data = self.generic_payload.copy()
        bad_data['requests'][0]['target']['longascnode'] = 4.0
        response = self.client.post(reverse('api:user_requests-list'), data=bad_data)
        self.assertEqual(response.status_code, 201)

    def test_post_userrequest_test_defaults(self):
        bad_data = self.generic_payload.copy()
        response = self.client.post(reverse('api:user_requests-list'), data=bad_data)
        self.assertEqual(response.status_code, 201)
        target = response.json()['requests'][0]['target']
        self.assertEqual(target['proper_motion_ra'], 0.0)
        self.assertEqual(target['proper_motion_dec'], 0.0)
        self.assertEqual(target['parallax'], 0.0)
        self.assertEqual(target['coordinate_system'], 'ICRS')
        self.assertEqual(target['equinox'], 'J2000')
        self.assertEqual(target['epoch'], 2000.0)

    def test_post_userrequest_test_proper_motion(self):
        bad_data = self.generic_payload.copy()
        bad_data['requests'][0]['target']['proper_motion_ra'] = 1.0
        bad_data['requests'][0]['target']['proper_motion_dec'] = 1.0
        # no epoch so it should fail
        response = self.client.post(reverse('api:user_requests-list'), data=bad_data)
        self.assertEqual(response.status_code, 400)

        bad_data['requests'][0]['target']['epoch'] = 2001.0
        response = self.client.post(reverse('api:user_requests-list'), data=bad_data)
        self.assertEqual(response.status_code, 201)


class TestNonSiderealTarget(APITestCase):
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
                    'type': 'NON_SIDEREAL',
                    'scheme'              : 'ASA_COMET',
                    # Non sidereal param
                    'epochofel'         : 57400.0,
                    'orbinc'            : 2.0,
                    'longascnode'       : 3.0,
                    'argofperih'        : 4.0,
                    'perihdist'         : 5.0,
                    'eccentricity'      : 0.99,
                    'epochofperih'      : 57400.0,
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

    def test_post_userrequest_non_sidereal_target(self):
        good_data = self.generic_payload.copy()
        response = self.client.post(reverse('api:user_requests-list'), data=good_data)
        self.assertEqual(response.status_code, 201)

    def test_post_userrequest_non_comet_eccentricity(self):
        bad_data = self.generic_payload.copy()
        bad_data['requests'][0]['target']['scheme'] = 'JPL_MINOR_PLANET'
        response = self.client.post(reverse('api:user_requests-list'), data=bad_data)
        self.assertEqual(response.status_code, 400)

        bad_data['requests'][0]['target']['eccentricity'] = 0.9
        response = self.client.post(reverse('api:user_requests-list'), data=bad_data)
        self.assertEqual(response.status_code, 201)


class TestSatelliteTarget(APITestCase):
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
                    'type': 'SATELLITE',
                    # satellite
                    'altitude'                  : 33.0,
                    'azimuth'                   : 2.0,
                    'diff_pitch_rate'           : 3.0,
                    'diff_roll_rate'            : 4.0,
                    'diff_pitch_acceleration'   : 5.0,
                    'diff_roll_acceleration'    : 0.99,
                    'diff_epoch_rate'           : 22.0,
                    'epoch'                     : 2000.0,
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

    def test_post_userrequest_satellite_target(self):
        good_data = self.generic_payload.copy()
        response = self.client.post(reverse('api:user_requests-list'), data=good_data)
        self.assertEqual(response.status_code, 201)


class TestLocationApi(APITestCase):
    def setUp(self):
        # patch the method for getting configdb data
        self.configdb_data = [
            {
                'code': 'tst',
                'enclosure_set': [
                    {
                        'code': 'doma',
                        'telescope_set': [
                            {
                                'code': '1m0a',
                            },
                        ]
                    },
                ]
            },
        ]

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
                    'dec': 34.4,
                    'ra': 20,
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

    @patch('valhalla.userrequests.serializers.get_configdb_data')
    def test_post_userrequest_all_location_info(self, get_cfg_data):
        get_cfg_data.return_value = self.configdb_data
        good_data = self.generic_payload.copy()
        good_data['requests'][0]['location']['site'] = 'tst'
        good_data['requests'][0]['location']['observatory'] = 'doma'
        good_data['requests'][0]['location']['telescope'] = '1m0a'
        response = self.client.post(reverse('api:user_requests-list'), data=good_data)
        self.assertEqual(response.status_code, 201)

    @patch('valhalla.userrequests.serializers.get_configdb_data')
    def test_post_userrequest_observatory_no_site(self, get_cfg_data):
        get_cfg_data.return_value = self.configdb_data
        good_data = self.generic_payload.copy()
        good_data['requests'][0]['location']['observatory'] = 'doma'
        good_data['requests'][0]['location']['telescope'] = '1m0a'
        response = self.client.post(reverse('api:user_requests-list'), data=good_data)
        self.assertEqual(response.status_code, 400)

    @patch('valhalla.userrequests.serializers.get_configdb_data')
    def test_post_userrequest_observatory_no_observatory(self, get_cfg_data):
        get_cfg_data.return_value = self.configdb_data
        good_data = self.generic_payload.copy()
        good_data['requests'][0]['location']['site'] = 'tst'
        good_data['requests'][0]['location']['telescope'] = '1m0a'
        response = self.client.post(reverse('api:user_requests-list'), data=good_data)
        self.assertEqual(response.status_code, 400)

    @patch('valhalla.userrequests.serializers.get_configdb_data')
    def test_post_userrequest_observatory_bad_observatory(self, get_cfg_data):
        get_cfg_data.return_value = self.configdb_data
        bad_data = self.generic_payload.copy()
        bad_data['requests'][0]['location']['site'] = 'tst'
        bad_data['requests'][0]['location']['observatory'] = 'domb'
        bad_data['requests'][0]['location']['telescope'] = '1m0a'
        response = self.client.post(reverse('api:user_requests-list'), data=bad_data)
        self.assertEqual(response.status_code, 400)

    @patch('valhalla.userrequests.serializers.get_configdb_data')
    def test_post_userrequest_observatory_bad_site(self, get_cfg_data):
        get_cfg_data.return_value = self.configdb_data
        bad_data = self.generic_payload.copy()
        bad_data['requests'][0]['location']['site'] = 'bpl'
        bad_data['requests'][0]['location']['observatory'] = 'doma'
        bad_data['requests'][0]['location']['telescope'] = '1m0a'
        response = self.client.post(reverse('api:user_requests-list'), data=bad_data)
        self.assertEqual(response.status_code, 400)

    @patch('valhalla.userrequests.serializers.get_configdb_data')
    def test_post_userrequest_observatory_bad_telescope(self, get_cfg_data):
        get_cfg_data.return_value = self.configdb_data
        bad_data = self.generic_payload.copy()
        bad_data['requests'][0]['location']['site'] = 'tst'
        bad_data['requests'][0]['location']['observatory'] = 'doma'
        bad_data['requests'][0]['location']['telescope'] = '1m0b'
        response = self.client.post(reverse('api:user_requests-list'), data=bad_data)
        self.assertEqual(response.status_code, 400)


class TestGetRequestApi(APITestCase):
    def setUp(self):
        self.proposal = mixer.blend(Proposal)
        self.user = mixer.blend(User, is_staff=False, is_superuser=False)
        self.staff_user = mixer.blend(User, is_staff=True)
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

    def test_get_request_list_staff(self):
        request = mixer.blend(Request, user_request=self.user_request, observation_note='testobsnote2')
        self.client.force_login(self.staff_user)
        result = self.client.get(reverse('api:requests-detail', args=(request.id,)))
        self.assertEquals(result.json()['observation_note'], request.observation_note)
