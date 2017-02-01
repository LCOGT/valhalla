from django.utils import timezone
from unittest.case import TestCase
from mixer.backend.django import mixer
from datetime import datetime
from unittest.mock import patch

from valhalla.userrequests.request_utils import (get_airmasses_for_request_at_sites, get_telescope_states_for_request)
from valhalla.userrequests.models import Request, Molecule, Target, UserRequest, Window, Location, Constraints
from valhalla.proposals.models import Proposal, TimeAllocation, Semester
from valhalla.common.test_telescope_states import TelescopeStatesFakeInput
from valhalla.common.test_helpers import ConfigDBTestMixin, SetTimeMixin


class BaseSetupRequest(ConfigDBTestMixin, SetTimeMixin, TestCase):
    def setUp(self):
        super().setUp()

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

        self.molecule_expose = mixer.blend(
            Molecule, request=self.request, bin_x=2, bin_y=2, instrument_name='1M0-SCICAM-SBIG',
            exposure_time=600, exposure_count=2, type='EXPOSE', filter='blah'
        )

        mixer.blend(Window, request=self.request, start=datetime(2016, 10, 1, tzinfo=timezone.utc),
                    end=datetime(2016, 10, 2, tzinfo=timezone.utc))

        mixer.blend(Target, request=self.request, type='SIDEREAL', ra=22, dec=-33,
                    proper_motion_ra=0.0, proper_motion_dec=0.0)

        self.location = mixer.blend(Location, request=self.request, telescope_class='1m0')
        mixer.blend(Constraints, request=self.request)


class TestRequestAirmass(BaseSetupRequest):
    def test_airmass_calculation(self):
        airmasses = get_airmasses_for_request_at_sites(self.request.as_dict)

        # Should be no data betwee 3:30AM and 18:30PM acording to pure rise set for this target, so verify that
        expected_null_range = (datetime(2016, 10, 1, 3, 30, 0), datetime(2016, 10, 1, 18, 30, 0))

        for airmass_time in airmasses['airmass_data']['tst']['times']:
            atime = datetime.strptime(airmass_time, '%Y-%m-%dT%H:%M')
            if atime > expected_null_range[0] and atime < expected_null_range[1]:
                self.fail("Should not get airmass ({}) within range {}".format(atime, expected_null_range))

    def test_airmass_calculation_empty(self):
        self.location.site = 'cpt'
        self.location.save()
        airmasses = get_airmasses_for_request_at_sites(self.request.as_dict)

        self.assertFalse(airmasses['airmass_data'])


class TestRequestTelescopeStates(TelescopeStatesFakeInput):
    def setUp(self):
        super().setUp()
        self.time_patcher = patch('valhalla.userrequests.serializers.timezone.now')
        self.mock_now = self.time_patcher.start()
        self.mock_now.return_value = datetime(2016, 10, 1, tzinfo=timezone.utc)
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

        self.molecule_expose = mixer.blend(
            Molecule, request=self.request, bin_x=2, bin_y=2, instrument_name='1M0-SCICAM-SBIG',
            exposure_time=600, exposure_count=2, type='EXPOSE', filter='blah'
        )

        mixer.blend(Window, request=self.request, start=datetime(2016, 10, 1, tzinfo=timezone.utc),
                    end=datetime(2016, 10, 2, tzinfo=timezone.utc))

        mixer.blend(Target, request=self.request, type='SIDEREAL', ra=22, dec=-33,
                    proper_motion_ra=0.0, proper_motion_dec=0.0)

        self.location = mixer.blend(Location, request=self.request, telescope_class='1m0')
        mixer.blend(Constraints, request=self.request)

    def tearDown(self):
        super().tearDown()
        self.time_patcher.stop()

        # super(BaseSetupRequest, self).tearDown()

    def test_telescope_states_calculation(self):
        telescope_states = get_telescope_states_for_request(self.request)
        # Assert that telescope states were received for this request
        self.assertIn(self.tk1, telescope_states)
        self.assertIn(self.tk2, telescope_states)

        expected_start_of_night = datetime(2016, 10, 1, 18, 45, 2, 760910, tzinfo=timezone.utc)

        # These are the same states tested for similar times in the telescope_states test class
        doma_expected_available_state = {'telescope': 'tst.doma.1m0a',
                                         'event_type': 'AVAILABLE',
                                         'event_reason': 'Available for scheduling',
                                         'start': expected_start_of_night,
                                         'end': datetime(2016, 10, 1, 20, 44, 58, tzinfo=timezone.utc)
                                         }

        self.assertIn(doma_expected_available_state, telescope_states[self.tk1])

        domb_expected_available_state1 = {'telescope': 'tst.domb.1m0a',
                                          'event_type': 'AVAILABLE',
                                          'event_reason': 'Available for scheduling',
                                          'start': expected_start_of_night,
                                          'end': datetime(2016, 10, 1, 19, 24, 59, tzinfo=timezone.utc)
                                          }

        self.assertIn(domb_expected_available_state1, telescope_states[self.tk2])

        domb_expected_available_state2 = {'telescope': 'tst.domb.1m0a',
                                          'event_type': 'AVAILABLE',
                                          'event_reason': 'Available for scheduling',
                                          'start': datetime(2016, 10, 1, 20, 24, 59, tzinfo=timezone.utc),
                                          'end': datetime(2016, 10, 1, 20, 44, 58, tzinfo=timezone.utc)
                                          }

        self.assertIn(domb_expected_available_state2, telescope_states[self.tk2])

    def test_telescope_states_empty(self):
        self.location.site = 'cpt'
        self.location.save()
        telescope_states = get_telescope_states_for_request(self.request)

        self.assertEqual({}, telescope_states)
