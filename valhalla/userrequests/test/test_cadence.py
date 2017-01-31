from unittest.case import TestCase
from mixer.backend.django import mixer
import datetime

from valhalla.common.test_helpers import ConfigDBTestMixin, SetTimeMixin
from valhalla.userrequests.cadence import get_cadence_requests
from valhalla.userrequests.models import Request, Molecule, Target, Constraints, Location


class TestCadence(SetTimeMixin, ConfigDBTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.req = mixer.blend(Request)
        self.molecule_expose = mixer.blend(
            Molecule, request=self.req, bin_x=2, bin_y=2, instrument_name='1M0-SCICAM-SBIG',
            exposure_time=10, exposure_count=1, type='EXPOSE', filter='air'
        )
        mixer.blend(Target, request=self.req, type='SIDEREAL', ra=34.4, dec=20,
                    proper_motion_ra=0.0, proper_motion_dec=0.0)
        mixer.blend(Constraints, request=self.req)
        mixer.blend(Location, request=self.req, telecope_class='1m0')

    def test_correct_number_of_requests_small_cadence(self):
        r_dict = self.req.as_dict
        r_dict['cadence'] = {
            'start': datetime.datetime(2016, 9, 1),
            'end': datetime.datetime(2016, 9, 3),
            'period': 24.0,
            'jitter': 12.0
        }

        requests = get_cadence_requests(r_dict)
        self.assertEqual(len(requests), 2)

    def test_correct_number_of_requests_large_cadence(self):
        r_dict = self.req.as_dict
        r_dict['cadence'] = {
            'start': datetime.datetime(2016, 9, 1),
            'end': datetime.datetime(2016, 10, 1),
            'period': 24.0,
            'jitter': 12.0
        }

        requests = get_cadence_requests(r_dict)
        self.assertEqual(len(requests), 26)

    def test_correct_number_of_requests_bounded_window(self):
        r_dict = self.req.as_dict
        r_dict['cadence'] = {
            'start': datetime.datetime(2016, 9, 1),
            'end': datetime.datetime(2016, 9, 2),
            'period': 24.0,
            'jitter': 12.0
        }

        requests = get_cadence_requests(r_dict)
        self.assertEqual(len(requests), 1)

    def test_correct_number_of_requests_overlapping_windows(self):
        r_dict = self.req.as_dict
        r_dict['cadence'] = {
            'start': datetime.datetime(2016, 9, 1),
            'end': datetime.datetime(2016, 9, 2),
            'period': 1.0,
            'jitter': 2.0
        }

        requests = get_cadence_requests(r_dict)
        self.assertEqual(len(requests), 5)
