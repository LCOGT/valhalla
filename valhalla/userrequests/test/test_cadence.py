from unittest.case import TestCase
from mixer.backend.django import mixer
import datetime

from valhalla.common.test_helpers import ConfigDBTestMixin
from valhalla.userrequests.cadence import get_cadence_requests
from valhalla.userrequests.models import Request, Molecule, Target, Constraints, Location


class TestCadence(TestCase, ConfigDBTestMixin):
    def test_correct_number_of_requests(self):
        r = mixer.blend(Request)
        mixer.blend(Molecule, instrument_name='1M0-SCICAM-SBIG', request=r)
        mixer.blend(Target, request=r)
        mixer.blend(Constraints, request=r)
        mixer.blend(Location, request=r)
        r_dict = r.as_dict
        r_dict['cadence'] = {
            'start': datetime.datetime(2016, 9, 1),
            'end': datetime.datetime(2016, 9, 3),
            'period': 24.0,
            'jitter': 12.0
        }

        requests = get_cadence_requests(r_dict)
        print(requests)
        self.assertEqual(len(requests), 2)
