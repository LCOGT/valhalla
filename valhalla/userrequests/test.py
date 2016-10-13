from valhalla.userrequests.models import Request, Molecule, Target, UserRequest, Window, Location
from valhalla.proposals.models import Proposal, TimeAllocation, Semester
from valhalla.common.configdb import ConfigDBException

from django.utils import timezone
from unittest.case import TestCase
from mixer.backend.django import mixer
from datetime import datetime
from unittest.mock import patch
import math

configdb_data = [
    {
        'code': 'tst',
        'enclosure_set': [
            {
                'code': 'doma',
                'telescope_set': [
                    {
                        'code': '1m0a',
                        'lat': -32.3805542,
                        'lon': 20.8100352,
                        'horizon': 15.0,
                        'ha_limit_pos': 4.6,
                        'ha_limit_neg': -4.6,
                        'instrument_set': [
                            {
                                'state': 'SCHEDULABLE',
                                'code': 'xx01',
                                'science_camera': {
                                    'camera_type': {
                                        'code': '1M0-SCICAM-SBIG',
                                        'name': '1M0-SCICAM-SBIG',
                                        'config_change_time': 0,
                                        'filter_change_time': 2,
                                        'fixed_overhead_per_exposure': 1,
                                        'front_padding': 90,
                                        'acquire_processing_time': 0,
                                        'acquire_exposure_time': 0,
                                        'default_mode': {
                                            'binning': 2,
                                            'readout': 14.5,
                                        },
                                        'mode_set': [
                                            {
                                                'binning': 1,
                                                'readout': 35,
                                            },
                                            {
                                                'binning': 2,
                                                'readout': 14.5,
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
                                        'filter_change_time': 0,
                                        'fixed_overhead_per_exposure': 0.5,
                                        'front_padding': 240,
                                        'acquire_processing_time': 60,
                                        'acquire_exposure_time': 30,
                                        'default_mode': {
                                            'binning': 1,
                                            'readout': 25,
                                        },
                                        'mode_set': [
                                            {
                                                'binning': 1,
                                                'readout': 25,
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
                        'lat': -32.3805542,
                        'lon': 20.8100352,
                        'horizon': 15.0,
                        'ha_limit_pos': 4.6,
                        'ha_limit_neg': -4.6,
                        'instrument_set': [
                        ]
                    },
                ]
            },
        ]
    },
]

class TestUserRequestTotalDuration(TestCase):
    def setUp(self):
        self.configdb_patcher = patch('valhalla.common.configdb.ConfigDB._get_configdb_data')
        self.mock_configdb = self.configdb_patcher.start()
        self.mock_configdb.return_value = configdb_data

        self.time_patcher = patch('valhalla.userrequests.serializers.timezone.now')
        self.mock_now = self.time_patcher.start()
        self.mock_now.return_value = datetime(2016, 9, 1, tzinfo=timezone.utc)

        self.proposal = mixer.blend(Proposal)
        semester = mixer.blend(Semester, id='2016B', start=datetime(2016, 9, 1, tzinfo=timezone.utc),
                               end=datetime(2016, 12, 31, tzinfo=timezone.utc)
                               )
        self.time_allocation_1m0 = mixer.blend(TimeAllocation, proposal=self.proposal, semester=semester,
                                               telescope_class='1m0', std_allocation=100.0, std_time_used=0.0,
                                               too_allocation=10, too_time_used=0.0, ipp_limit=10.0,
                                               ipp_time_available=5.0)

        self.ur_single = mixer.blend(UserRequest, proposal=self.proposal, operator='SINGLE')

        self.request = mixer.blend(Request, user_request=self.ur_single)

        self.ur_many = mixer.blend(UserRequest, proposal=self.proposal)

        self.request_1 = mixer.blend(Request, user_request=self.ur_many)
        self.request_2 = mixer.blend(Request, user_request=self.ur_many)
        self.request_3 = mixer.blend(Request, user_request=self.ur_many)

        self.molecule_expose = mixer.blend(
            Molecule, request=self.request, bin_x=2, bin_y=2, instrument_name='1M0-SCICAM-SBIG',
            exposure_time=600, exposure_count=2, type='EXPOSE', filter='blah'
        )

        self.molecule_expose_1 = mixer.blend(
            Molecule, request=self.request_1, bin_x=2, bin_y=2, instrument_name='1M0-SCICAM-SBIG',
            exposure_time=1000, exposure_count=1, type='EXPOSE', filter='uv'
        )

        self.molecule_expose_2 = mixer.blend(
            Molecule, request=self.request_2, bin_x=2, bin_y=2, instrument_name='1M0-SCICAM-SBIG',
            exposure_time=10, exposure_count=5, type='EXPOSE', filter='uv'
        )

        self.molecule_expose_3 = mixer.blend(
            Molecule, request=self.request_3, bin_x=2, bin_y=2, instrument_name='1M0-SCICAM-SBIG',
            exposure_time=3, exposure_count=3, type='EXPOSE', filter='ir'
        )
        mixer.blend(Window, request=self.request, start=datetime(2016, 9, 29, tzinfo=timezone.utc),
                    end=datetime(2016, 10, 29, tzinfo=timezone.utc))
        mixer.blend(Window, request=self.request_1, start=datetime(2016, 9, 29, tzinfo=timezone.utc),
                    end=datetime(2016, 10, 29, tzinfo=timezone.utc))
        mixer.blend(Window, request=self.request_2, start=datetime(2016, 9, 29, tzinfo=timezone.utc),
                    end=datetime(2016, 10, 29, tzinfo=timezone.utc))
        mixer.blend(Window, request=self.request_3, start=datetime(2016, 9, 29, tzinfo=timezone.utc),
                    end=datetime(2016, 10, 29, tzinfo=timezone.utc))
        mixer.blend(Location, request=self.request, telescope_class='1m0')
        mixer.blend(Location, request=self.request_1, telescope_class='1m0')
        mixer.blend(Location, request=self.request_2, telescope_class='1m0')
        mixer.blend(Location, request=self.request_3, telescope_class='1m0')

    def tearDown(self):
        self.configdb_patcher.stop()
        self.time_patcher.stop()

    def test_single_ur_total_duration(self):
        request_duration = self.request.duration
        total_duration = self.ur_single.total_duration
        tak = self.request.time_allocation_key
        self.assertEqual(request_duration, total_duration[tak])

    def test_many_ur_takes_highest_duration(self):
        self.ur_many.operator = 'MANY'
        self.ur_many.save()

        highest_duration = max(self.request_1.duration, self.request_2.duration, self.request_3.duration)
        total_duration = self.ur_many.total_duration
        tak = self.request_1.time_allocation_key
        self.assertEqual(highest_duration, total_duration[tak])

    def test_and_ur_takes_sum_of_durations(self):
        self.ur_many.operator = 'AND'
        self.ur_many.save()

        sum_duration = self.request_1.duration + self.request_2.duration + self.request_3.duration
        total_duration = self.ur_many.total_duration
        tak = self.request_1.time_allocation_key
        self.assertEqual(sum_duration, total_duration[tak])


class TestRequestDuration(TestCase):
    def setUp(self):
        self.configdb_patcher = patch('valhalla.common.configdb.ConfigDB._get_configdb_data')
        self.mock_configdb = self.configdb_patcher.start()
        self.mock_configdb.return_value = configdb_data

        self.time_patcher = patch('valhalla.userrequests.serializers.timezone.now')
        self.mock_now = self.time_patcher.start()
        self.mock_now.return_value = datetime(2016, 9, 1, tzinfo=timezone.utc)

        self.target_acquire_on = mixer.blend(Target, acquire_mode='ON')

        self.target_acquire_off = mixer.blend(Target, acquire_mode='OFF')

        self.molecule_expose = mixer.blend(
            Molecule, bin_x=2, bin_y=2, instrument_name='1M0-SCICAM-SBIG',
            exposure_time=600, exposure_count=2, type='EXPOSE', filter='blah'
        )

        self.molecule_expose_1 = mixer.blend(
            Molecule, bin_x=2, bin_y=2, instrument_name='1M0-SCICAM-SBIG',
            exposure_time=1000, exposure_count=1, type='EXPOSE', filter='uv'
        )

        self.molecule_expose_2 = mixer.blend(
            Molecule, bin_x=2, bin_y=2, instrument_name='1M0-SCICAM-SBIG',
            exposure_time=10, exposure_count=5, type='EXPOSE', filter='uv'
        )

        self.molecule_expose_3 = mixer.blend(
            Molecule, bin_x=2, bin_y=2, instrument_name='1M0-SCICAM-SBIG',
            exposure_time=3, exposure_count=3, type='EXPOSE', filter='ir'
        )

        self.molecule_spectrum = mixer.blend(
            Molecule, bin_x=1, bin_y=1, instrument_name='2M0-FLOYDS-SCICAM',
            exposure_time=1800, exposure_count=1, type='SPECTRUM'
        )

        self.molecule_arc = mixer.blend(
            Molecule, bin_x=1, bin_y=1, instrument_name='2M0-FLOYDS-SCICAM',
            exposure_time=30, exposure_count=2, type='ARC'
        )

        self.molecule_lampflat = mixer.blend(
            Molecule, bin_x=1, bin_y=1, instrument_name='2M0-FLOYDS-SCICAM',
            exposure_time=60, exposure_count=1, type='LAMPFLAT'
        )

    def tearDown(self):
        self.configdb_patcher.stop()
        self.time_patcher.stop()

    def test_ccd_single_molecule_request_duration(self):
        request = mixer.blend(Request)
        self.molecule_expose.request = request
        self.molecule_expose.save()
        duration = request.duration

        self.assertEqual(duration, math.ceil(2*600 + 90 + 2*14.5 + 2*1 + 2 + 5 + 11))

    def test_ccd_single_molecule_duration(self):
        duration = self.molecule_expose.duration

        self.assertEqual(duration, (2*600 + 2*14.5 + 2 + 5 + 11))

    def test_ccd_multiple_molecule_request_duration(self):
        request = mixer.blend(Request)
        self.molecule_expose_1.request = request
        self.molecule_expose_1.save()
        self.molecule_expose_2.request = request
        self.molecule_expose_2.save()
        self.molecule_expose_3.request = request
        self.molecule_expose_3.save()
        duration = request.duration

        self.assertEqual(duration, math.ceil(1000 + 5*10 + 3*3 + 90 + 9*14.5 + 9*1 + 2*2 + 3*5 + 3*11))

    def test_ccd_multiple_molecule_duration(self):
        duration = self.molecule_expose_1.duration
        duration += self.molecule_expose_2.duration
        duration += self.molecule_expose_3.duration

        self.assertEqual(duration, (1000 + 5*10 + 3*3 + 9*14.5 + 9*1 + 3*5 + 3*11))

    def test_floyds_single_molecule_request_duration_with_acquire_on(self):
        request = mixer.blend(Request, target=self.target_acquire_on)
        self.molecule_spectrum.request = request
        self.molecule_spectrum.save()

        duration = request.duration

        self.assertEqual(duration, math.ceil(1800 + 240 + 25 + 0.5 + 30 + 30 + 60 + 5 + 11))

    def test_floyds_single_molecule_request_duration_with_acquire_off(self):
        request = mixer.blend(Request, target=self.target_acquire_off)
        self.molecule_spectrum.request = request
        self.molecule_spectrum.save()

        duration = request.duration

        self.assertEqual(duration, math.ceil(1800 + 240 + 25 + 0.5 + 30 + 5 + 11))

    def test_floyds_single_molecule_duration(self):
        duration = self.molecule_spectrum.duration

        self.assertEqual(duration, (1800 + 25 + 0.5 + 5 + 11))

    def test_floyds_multiple_molecule_request_duration_with_acquire_on(self):
        request = mixer.blend(Request, target=self.target_acquire_on)
        self.molecule_lampflat.request = request
        self.molecule_lampflat.save()
        self.molecule_arc.request = request
        self.molecule_arc.save()
        self.molecule_spectrum.request = request
        self.molecule_spectrum.save()

        duration = request.duration

        self.assertEqual(duration, math.ceil(1800 + 60 + 2*30 + 240 + 4*25 + 4*0.5 + 30*3 + 30 + 60 + 3*5 + 3*11))

    def test_floyds_multiple_molecule_request_duration_with_acquire_off(self):
        request = mixer.blend(Request, target=self.target_acquire_off)
        self.molecule_lampflat.request = request
        self.molecule_lampflat.save()
        self.molecule_arc.request = request
        self.molecule_arc.save()
        self.molecule_spectrum.request = request
        self.molecule_spectrum.save()

        duration = request.duration

        self.assertEqual(duration, math.ceil(1800 + 60 + 2*30 + 240 + 4*25 + 4*0.5 + 30*3 + 3*5 + 3*11))

    def test_floyds_multiple_molecule_duration(self):
        duration = self.molecule_lampflat.duration
        duration += self.molecule_arc.duration
        duration += self.molecule_spectrum.duration

        self.assertEqual(duration, (1800 + 60 + 2*30 + 4*25 + 4*0.5 + 3*5 + 3*11))

    def test_get_duration_from_non_existent_camera(self):
        bad_molecule = mixer.blend(Molecule, instrument_name='FAKE_INSTRUMENT', bin_x=1, bin_y=1)

        with self.assertRaises(ConfigDBException) as context:
            bad_molecule.duration
            self.assertTrue('not found in configdb' in context.exception)
