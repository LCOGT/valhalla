from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from valhalla.userrequests.models import UserRequest, Request
from valhalla.proposals.models import Proposal, Membership, TimeAllocation, Semester
from rest_framework.test import APITestCase

from mixer.backend.django import mixer
from unittest.mock import patch
from django.utils import timezone
from datetime import datetime
import copy

import valhalla.userrequests.signals.handlers


configdb_data = [
    {
        'code': 'tst',
        'enclosure_set': [
            {
                'code': 'doma',
                'telescope_set': [
                    {
                        'code': '1m0a',
                        'instrument_set': [
                            {
                                'state': 'SCHEDULABLE',
                                'code': 'xx01',
                                'science_camera': {
                                    'camera_type': {
                                        'code': '1M0-SCICAM-SBIG',
                                        'name': '1M0-SCICAM-SBIG',
                                        'default_mode': {
                                            'binning': 2,
                                            'readout': 14,
                                        },
                                        'config_change_time': 30,
                                        'acquire_processing_time': 30,
                                        'acquire_exposure_time': 30,
                                        'front_padding': 90,
                                        'filter_change_time': 2,
                                        'fixed_overhead_per_exposure': 1,
                                        'mode_set': [
                                            {
                                                'binning': 1,
                                                'readout': 33,
                                            },
                                            {
                                                'binning': 2,
                                                'readout': 14,
                                            },
                                        ]
                                    },
                                    'filters': 'air',
                                },
                                '__str__': 'tst.doma.1m0a.xx01-xx01',
                            },
                            {
                                'state': 'SCHEDULABLE',
                                'code': 'xx02',
                                'science_camera': {
                                    'camera_type': {
                                        'code': '2M0-FLOYDS-SCICAM',
                                        'name': '2M0-FLOYDS-SCICAM',
                                        'config_change_time': 30,
                                        'acquire_processing_time': 30,
                                        'acquire_exposure_time': 30,
                                        'front_padding': 90,
                                        'filter_change_time': 2,
                                        'fixed_overhead_per_exposure': 1,
                                        'default_mode': {
                                            'binning': 1,
                                            'readout': 33,
                                        },
                                        'mode_set': [
                                            {
                                                'binning': 1,
                                                'readout': 33,
                                            },
                                        ]
                                    },
                                    'filters': 'slit_1.2as,floyds_slit_default',
                                },
                                '__str__': 'tst.doma.1m0a.xx02-xx02',
                            },
                        ]
                    },
                ]
            },
        ]
    },
        {
        'code': 'non',
        'enclosure_set': [
            {
                'code': 'doma',
                'telescope_set': [
                    {
                        'code': '1m0a',
                        'instrument_set': [
                        ]
                    },
                ]
            },
        ]
    },
]

generic_payload = {
    'proposal': 'temp',
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
            'instrument_name': '1M0-SCICAM-SBIG',
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


class TestUserGetRequestApi(APITestCase):
    def setUp(self):
        self.configdb_patcher = patch('valhalla.common.configdb.ConfigDB._get_configdb_data')
        self.mock_configdb = self.configdb_patcher.start()
        self.mock_configdb.return_value = configdb_data

        self.proposal = mixer.blend(Proposal)
        self.user = mixer.blend(User, is_staff=False, is_superuser=False)
        self.other_user = mixer.blend(User, is_staff=False, is_superuser=False)
        mixer.blend(Membership, user=self.user, proposal=self.proposal)
        self.staff_user = mixer.blend(User, is_staff=True)

    def tearDown(self):
        self.configdb_patcher.stop()

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
        self.configdb_patcher = patch('valhalla.common.configdb.ConfigDB._get_configdb_data')
        self.mock_configdb = self.configdb_patcher.start()
        self.mock_configdb.return_value = configdb_data

        self.proposal = mixer.blend(Proposal)
        self.user = mixer.blend(User)
        self.client.force_login(self.user)

        mixer.blend(Membership, user=self.user, proposal=self.proposal)
        self.generic_payload = copy.deepcopy(generic_payload)
        self.generic_payload['proposal'] = self.proposal.id

    def tearDown(self):
        self.configdb_patcher.stop()

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


class TestUserPostRequestIPPApi(APITestCase):
    def setUp(self):
        self.configdb_patcher = patch('valhalla.common.configdb.ConfigDB._get_configdb_data')
        self.mock_configdb = self.configdb_patcher.start()
        self.mock_configdb.return_value = configdb_data

        self.proposal = mixer.blend(Proposal)
        self.user = mixer.blend(User)
        self.client.force_login(self.user)

        mixer.blend(Membership, user=self.user, proposal=self.proposal)

        semester = mixer.blend(Semester, id='2016B', start=datetime(2016, 9, 1, tzinfo=timezone.utc), end=datetime(2016, 12, 31, tzinfo=timezone.utc))

        self.time_allocation_1m0 = mixer.blend(TimeAllocation, proposal=self.proposal, semester=semester,
                                               telescope_class='1m0', std_allocation=100.0, std_time_used=0.0,
                                               too_allocation=10, too_time_used=0.0, ipp_limit=10.0,
                                               ipp_time_available=5.0)

        self.generic_payload = copy.deepcopy(generic_payload)
        self.generic_payload['ipp_value'] = 1.5
        self.generic_payload['proposal'] = self.proposal.id

    def tearDown(self):
        self.configdb_patcher.stop()

    def test_user_request_debit_ipp_on_creation(self):
        self.assertEqual(self.time_allocation_1m0.ipp_time_available, 5.0)

        ur = self.generic_payload.copy()
        response = self.client.post(reverse('api:user_requests-list'), data=ur)
        self.assertEqual(response.status_code, 201)

        # verify that now that the object is saved, ipp has been debited
        time_allocation = TimeAllocation.objects.get(pk=self.time_allocation_1m0.id)
        self.assertLess(time_allocation.ipp_time_available, 5.0)

    def test_user_request_debit_ipp_on_creation_fail(self):
        self.assertEqual(self.time_allocation_1m0.ipp_time_available, 5.0)

        ur = self.generic_payload.copy()
        #ipp value that is too high, will be rejected
        ur['ipp_value'] = 100.0
        response = self.client.post(reverse('api:user_requests-list'), data=ur)
        self.assertEqual(response.status_code, 400)
        self.assertIn('TimeAllocationError', str(response.content))

        # verify that objects were not created by the send
        self.assertEqual(len(UserRequest.objects.filter(ipp_value=100.0)), 0)


class TestWindowApi(APITestCase):
    def setUp(self):
        self.configdb_patcher = patch('valhalla.common.configdb.ConfigDB._get_configdb_data')
        self.mock_configdb = self.configdb_patcher.start()
        self.mock_configdb.return_value = configdb_data

        self.proposal = mixer.blend(Proposal)
        self.user = mixer.blend(User)
        self.client.force_login(self.user)

        mixer.blend(Membership, user=self.user, proposal=self.proposal)
        self.generic_payload = copy.deepcopy(generic_payload)
        self.generic_payload['proposal'] = self.proposal.id

    def tearDown(self):
        self.configdb_patcher.stop()

    def test_post_userrequest_window_end_before_start(self):
        bad_data = self.generic_payload.copy()
        bad_data['requests'][0]['windows'][0]['end'] = '2016-09-28T21:12:18Z'
        response = self.client.post(reverse('api:user_requests-list'), data=bad_data)
        self.assertEqual(response.status_code, 400)


class TestSiderealTarget(APITestCase):
    def setUp(self):
        self.configdb_patcher = patch('valhalla.common.configdb.ConfigDB._get_configdb_data')
        self.mock_configdb = self.configdb_patcher.start()
        self.mock_configdb.return_value = configdb_data

        self.proposal = mixer.blend(Proposal)
        self.user = mixer.blend(User)
        self.client.force_login(self.user)

        mixer.blend(Membership, user=self.user, proposal=self.proposal)
        self.generic_payload = copy.deepcopy(generic_payload)
        self.generic_payload['proposal'] = self.proposal.id

    def tearDown(self):
        self.configdb_patcher.stop()

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
        self.configdb_patcher = patch('valhalla.common.configdb.ConfigDB._get_configdb_data')
        self.mock_configdb = self.configdb_patcher.start()
        self.mock_configdb.return_value = configdb_data

        self.proposal = mixer.blend(Proposal)
        self.user = mixer.blend(User)
        self.client.force_login(self.user)

        mixer.blend(Membership, user=self.user, proposal=self.proposal)
        self.generic_payload = copy.deepcopy(generic_payload)
        self.generic_payload['proposal'] = self.proposal.id
        self.generic_payload['requests'][0]['target'] = {
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
                                                        }

    def tearDown(self):
        self.configdb_patcher.stop()

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
        self.configdb_patcher = patch('valhalla.common.configdb.ConfigDB._get_configdb_data')
        self.mock_configdb = self.configdb_patcher.start()
        self.mock_configdb.return_value = configdb_data

        self.proposal = mixer.blend(Proposal)
        self.user = mixer.blend(User)
        self.client.force_login(self.user)

        mixer.blend(Membership, user=self.user, proposal=self.proposal)
        self.generic_payload = copy.deepcopy(generic_payload)
        self.generic_payload['proposal'] = self.proposal.id
        self.generic_payload['requests'][0]['target'] = {
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
                                                         }

    def tearDown(self):
        self.configdb_patcher.stop()

    def test_post_userrequest_satellite_target(self):
        good_data = self.generic_payload.copy()
        response = self.client.post(reverse('api:user_requests-list'), data=good_data)
        self.assertEqual(response.status_code, 201)


class TestLocationApi(APITestCase):
    def setUp(self):
        self.configdb_patcher = patch('valhalla.common.configdb.ConfigDB._get_configdb_data')
        self.mock_configdb = self.configdb_patcher.start()
        self.mock_configdb.return_value = configdb_data

        self.proposal = mixer.blend(Proposal)
        self.user = mixer.blend(User)
        self.client.force_login(self.user)

        mixer.blend(Membership, user=self.user, proposal=self.proposal)
        self.generic_payload = copy.deepcopy(generic_payload)
        self.generic_payload['proposal'] = self.proposal.id

    def tearDown(self):
        self.configdb_patcher.stop()

    def test_post_userrequest_all_location_info(self):
        good_data = self.generic_payload.copy()
        good_data['requests'][0]['location']['site'] = 'tst'
        good_data['requests'][0]['location']['observatory'] = 'doma'
        good_data['requests'][0]['location']['telescope'] = '1m0a'
        response = self.client.post(reverse('api:user_requests-list'), data=good_data)
        self.assertEqual(response.status_code, 201)

    def test_post_userrequest_observatory_no_site(self):
        good_data = self.generic_payload.copy()
        good_data['requests'][0]['location']['observatory'] = 'doma'
        good_data['requests'][0]['location']['telescope'] = '1m0a'
        response = self.client.post(reverse('api:user_requests-list'), data=good_data)
        self.assertEqual(response.status_code, 400)

    def test_post_userrequest_observatory_no_observatory(self):
        good_data = self.generic_payload.copy()
        good_data['requests'][0]['location']['site'] = 'tst'
        good_data['requests'][0]['location']['telescope'] = '1m0a'
        response = self.client.post(reverse('api:user_requests-list'), data=good_data)
        self.assertEqual(response.status_code, 400)

    def test_post_userrequest_observatory_bad_observatory(self):
        bad_data = self.generic_payload.copy()
        bad_data['requests'][0]['location']['site'] = 'tst'
        bad_data['requests'][0]['location']['observatory'] = 'domb'
        bad_data['requests'][0]['location']['telescope'] = '1m0a'
        response = self.client.post(reverse('api:user_requests-list'), data=bad_data)
        self.assertEqual(response.status_code, 400)

    def test_post_userrequest_observatory_bad_site(self):
        bad_data = self.generic_payload.copy()
        bad_data['requests'][0]['location']['site'] = 'bpl'
        bad_data['requests'][0]['location']['observatory'] = 'doma'
        bad_data['requests'][0]['location']['telescope'] = '1m0a'
        response = self.client.post(reverse('api:user_requests-list'), data=bad_data)
        self.assertEqual(response.status_code, 400)

    def test_post_userrequest_observatory_bad_telescope(self):
        bad_data = self.generic_payload.copy()
        bad_data['requests'][0]['location']['site'] = 'tst'
        bad_data['requests'][0]['location']['observatory'] = 'doma'
        bad_data['requests'][0]['location']['telescope'] = '1m0b'
        response = self.client.post(reverse('api:user_requests-list'), data=bad_data)
        self.assertEqual(response.status_code, 400)


class TestMoleculeApi(APITestCase):
    def setUp(self):
        self.configdb_patcher = patch('valhalla.common.configdb.ConfigDB._get_configdb_data')
        self.mock_configdb = self.configdb_patcher.start()
        self.mock_configdb.return_value = configdb_data

        self.proposal = mixer.blend(Proposal)
        self.user = mixer.blend(User)
        self.client.force_login(self.user)

        mixer.blend(Membership, user=self.user, proposal=self.proposal)
        self.generic_payload = copy.deepcopy(generic_payload)
        self.generic_payload['proposal'] = self.proposal.id

    def tearDown(self):
        self.configdb_patcher.stop()

    def test_default_ag_mode_for_spectrograph(self):
        good_data = self.generic_payload.copy()
        response = self.client.post(reverse('api:user_requests-list'), data=good_data)
        self.assertEqual(response.status_code, 201)
        molecule = response.json()['requests'][0]['molecules'][0]
        # check that without spectral instrument, these defaults are different
        self.assertEqual(molecule['ag_mode'], 'OPTIONAL')
        self.assertEqual(molecule['spectra_slit'], '')

        good_data['requests'][0]['molecules'][0]['instrument_name'] = '2M0-FLOYDS-SCICAM'
        response = self.client.post(reverse('api:user_requests-list'), data=good_data)
        self.assertEqual(response.status_code, 201)
        molecule = response.json()['requests'][0]['molecules'][0]
        # now with spectral instrument, defaults have changed
        self.assertEqual(molecule['ag_mode'], 'ON')
        self.assertEqual(molecule['spectra_slit'], 'floyds_slit_default')

    def test_invalid_filter_for_instrument(self):
        bad_data = self.generic_payload.copy()
        bad_data['requests'][0]['molecules'][0]['filter'] = 'magic'
        response = self.client.post(reverse('api:user_requests-list'), data=bad_data)
        self.assertIn('Invalid filter', str(response.content))
        self.assertEqual(response.status_code, 400)

    def test_filter_not_necessary_for_type(self):
        good_data = self.generic_payload.copy()
        good_data['requests'][0]['molecules'][0]['type'] = 'ARC'
        del good_data['requests'][0]['molecules'][0]['filter']
        response = self.client.post(reverse('api:user_requests-list'), data=good_data)
        self.assertEqual(response.status_code, 201)

    def test_invalid_spectra_slit_for_instrument(self):
        bad_data = self.generic_payload.copy()
        bad_data['requests'][0]['molecules'][0]['instrument_name'] = '2M0-FLOYDS-SCICAM'
        del bad_data['requests'][0]['molecules'][0]['filter']
        bad_data['requests'][0]['molecules'][0]['spectra_slit'] = 'slit_really_small'
        response = self.client.post(reverse('api:user_requests-list'), data=bad_data)
        self.assertIn('Invalid spectra slit', str(response.content))
        self.assertEqual(response.status_code, 400)

    def test_invalid_binning_for_instrument(self):
        bad_data = self.generic_payload.copy()
        bad_data['requests'][0]['molecules'][0]['bin_x'] = 5
        bad_data['requests'][0]['molecules'][0]['bin_y'] = 5
        response = self.client.post(reverse('api:user_requests-list'), data=bad_data)
        self.assertIn('Invalid binning', str(response.content))
        self.assertEqual(response.status_code, 400)

    def test_default_binning_for_instrument(self):
        good_data = self.generic_payload.copy()
        del good_data['requests'][0]['molecules'][0]['bin_x']
        del good_data['requests'][0]['molecules'][0]['bin_y']
        response = self.client.post(reverse('api:user_requests-list'), data=good_data)
        self.assertEqual(response.status_code, 201)
        molecule = response.json()['requests'][0]['molecules'][0]
        self.assertEqual(molecule['bin_x'], 2)
        self.assertEqual(molecule['bin_y'], 2)

    def test_must_set_both_binnings(self):
        bad_data = self.generic_payload.copy()
        del bad_data['requests'][0]['molecules'][0]['bin_x']
        response = self.client.post(reverse('api:user_requests-list'), data=bad_data)
        self.assertIn('Missing one of bin_x or bin_y', str(response.content))
        self.assertEqual(response.status_code, 400)

    def test_request_invalid_instrument_name(self):
        bad_data = self.generic_payload.copy()
        bad_data['requests'][0]['molecules'][0]['instrument_name'] = 'FAKE-INSTRUMENT'
        response = self.client.post(reverse('api:user_requests-list'), data=bad_data)
        self.assertIn('Invalid instrument name', str(response.content))
        self.assertEqual(response.status_code, 400)

    def test_request_invalid_instrument_name_for_location(self):
        bad_data = self.generic_payload.copy()
        bad_data['requests'][0]['location']['site'] = 'non'
        response = self.client.post(reverse('api:user_requests-list'), data=bad_data)
        self.assertIn("Invalid instrument name \\\'1M0-SCICAM-SBIG\\\' at site", str(response.content))
        self.assertEqual(response.status_code, 400)


class TestGetRequestApi(APITestCase):
    def setUp(self):
        self.configdb_patcher = patch('valhalla.common.configdb.ConfigDB._get_configdb_data')
        self.mock_configdb = self.configdb_patcher.start()
        self.mock_configdb.return_value = configdb_data

        self.proposal = mixer.blend(Proposal)
        self.user = mixer.blend(User, is_staff=False, is_superuser=False)
        self.staff_user = mixer.blend(User, is_staff=True)
        mixer.blend(Membership, user=self.user, proposal=self.proposal)
        self.user_request = mixer.blend(UserRequest, submitter=self.user, proposal=self.proposal)

    def tearDown(self):
        self.configdb_patcher.stop()

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


