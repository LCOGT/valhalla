from valhalla.common.telescope_states import get_telescope_states, get_telescope_availability_per_day
from valhalla.common.test_configdb import configdb_data
from valhalla.common.configdb import TelescopeKey

from django.test import TestCase
from datetime import datetime
from django.utils import timezone
from unittest.mock import patch, MagicMock
import json


class TestTelescopeStates(TestCase):
    def setUp(self):
        self.configdb_patcher = patch('valhalla.common.configdb.ConfigDB._get_configdb_data')
        self.mock_configdb = self.configdb_patcher.start()
        self.mock_configdb.return_value = configdb_data

        self.es_output = [
            {
                '_source': {
                    'type': 'AVAILABLE',
                    'timestamp': '2016-10-01 15:24:58',
                    'site': 'tst',
                    'telescope': '1m0a',
                    'reason': 'Available for scheduling',
                    'enclosure': 'doma',
                }
            },
            {
                '_source': {
                    'type': 'AVAILABLE',
                    'timestamp': '2016-10-01 15:30:00',
                    'site': 'tst',
                    'telescope': '1m0a',
                    'reason': 'Available for scheduling',
                    'enclosure': 'domb',
                }
            },
            {
                '_source': {
                    'type': 'AVAILABLE',
                    'timestamp': '2016-10-01 16:24:58',
                    'site': 'tst',
                    'telescope': '1m0a',
                    'reason': 'Available for scheduling',
                    'enclosure': 'doma',
                }
            },
            {
                '_source': {
                    'type': 'SEQUENCER_UNAVAILABLE',
                    'timestamp': '2016-10-01 16:24:59',
                    'site': 'tst',
                    'telescope': '1m0a',
                    'reason': 'It is broken',
                    'enclosure': 'domb',
                }
            },
            {
                '_source': {
                    'type': 'ENCLOSURE_INTERLOCK',
                    'timestamp': '2016-10-01 16:24:59',
                    'site': 'tst',
                    'telescope': '1m0a',
                    'reason': 'It is locked',
                    'enclosure': 'domb',
                }
            },
            {
                '_source': {
                    'type': 'AVAILABLE',
                    'timestamp': '2016-10-01 17:24:58',
                    'site': 'tst',
                    'telescope': '1m0a',
                    'reason': 'Available for scheduling',
                    'enclosure': 'doma',
                }
            },
            {
                '_source': {
                    'type': 'AVAILABLE',
                    'timestamp': '2016-10-01 17:24:59',
                    'site': 'tst',
                    'telescope': '1m0a',
                    'reason': 'Available for scheduling',
                    'enclosure': 'domb',
                }
            },
            {
                '_source': {
                    'type': 'BUG',
                    'timestamp': '2016-10-01 17:44:58',
                    'site': 'tst',
                    'telescope': '1m0a',
                    'reason': 'Bad bug ruins everything',
                    'enclosure': 'doma',
                }
            },
            {
                '_source': {
                    'type': 'BUG',
                    'timestamp': '2016-10-01 17:44:58',
                    'site': 'tst',
                    'telescope': '1m0a',
                    'reason': 'Bad bug ruins everything',
                    'enclosure': 'domb',
                }
            },
        ]

        self.tk1 = TelescopeKey('tst', 'doma', '1m0a')
        self.tk2 = TelescopeKey('tst', 'domb', '1m0a')

        self.es_patcher = patch('valhalla.common.telescope_states.get_es_data')
        self.mock_es = self.es_patcher.start()
        self.mock_es.return_value = self.es_output

    def tearDown(self):
        self.configdb_patcher.stop()
        self.es_patcher.stop()

    def test_aggregate_states_1(self):
        start = datetime(2016, 10, 1)
        end = datetime(2016, 10, 2)
        telescope_states = get_telescope_states(start, end)

        self.assertIn(self.tk1, telescope_states)
        self.assertIn(self.tk2, telescope_states)

        doma_expected_available_state = {'telescope': 'tst.doma.1m0a',
                                         'event_type': 'AVAILABLE',
                                         'event_reason': 'Available for scheduling',
                                         'start': datetime(2016, 10, 1, 15, 24, 58, tzinfo=timezone.utc),
                                         'end': datetime(2016, 10, 1, 17, 44, 58, tzinfo=timezone.utc)
                                         }

        self.assertIn(doma_expected_available_state, telescope_states[self.tk1])

        domb_expected_available_state1 = {'telescope': 'tst.domb.1m0a',
                                          'event_type': 'AVAILABLE',
                                          'event_reason': 'Available for scheduling',
                                          'start': datetime(2016, 10, 1, 15, 30, 0, tzinfo=timezone.utc),
                                          'end': datetime(2016, 10, 1, 16, 24, 59, tzinfo=timezone.utc)
                                          }

        self.assertIn(domb_expected_available_state1, telescope_states[self.tk2])

        domb_expected_available_state2 = {'telescope': 'tst.domb.1m0a',
                                          'event_type': 'AVAILABLE',
                                          'event_reason': 'Available for scheduling',
                                          'start': datetime(2016, 10, 1, 17, 24, 59, tzinfo=timezone.utc),
                                          'end': datetime(2016, 10, 1, 17, 44, 58, tzinfo=timezone.utc)
                                          }
        self.assertIn(domb_expected_available_state2, telescope_states[self.tk2])

    @patch('valhalla.common.telescope_states.get_site_rise_set_intervals')
    def test_telescope_availability_limits_interval(self, mock_intervals):
        mock_intervals.return_value = [(datetime(2016, 9, 30, 15, 30, 0, tzinfo=timezone.utc),
                                        datetime(2016, 9, 30, 18, 0, 0, tzinfo=timezone.utc)),
                                       (datetime(2016, 10, 1, 15, 30, 0, tzinfo=timezone.utc),
                                        datetime(2016, 10, 1, 18, 0, 0, tzinfo=timezone.utc)),
                                       (datetime(2016, 10, 2, 15, 30, 0, tzinfo=timezone.utc),
                                        datetime(2016, 10, 2, 18, 0, 0, tzinfo=timezone.utc))]
        start = datetime(2016, 9, 30, tzinfo=timezone.utc)
        end = datetime(2016, 10, 2, tzinfo=timezone.utc)
        telescope_availability = get_telescope_availability_per_day(start, end)

        self.assertIn(self.tk1, telescope_availability)
        self.assertIn(self.tk2, telescope_availability)

        doma_available_time = (datetime(2016, 10, 1, 17, 44, 58) - datetime(2016, 10, 1, 15, 30, 0)).total_seconds()
        doma_total_time = (datetime(2016, 10, 1, 18, 0, 0) - datetime(2016, 10, 1, 15, 30, 0)).total_seconds()

        doma_expected_availability = doma_available_time / doma_total_time
        self.assertAlmostEqual(doma_expected_availability, telescope_availability[self.tk1][0][1])

        domb_available_time = (datetime(2016, 10, 1, 16, 24, 59) - datetime(2016, 10, 1, 15, 30, 0)).total_seconds()
        domb_available_time += (datetime(2016, 10, 1, 17, 44, 58) - datetime(2016, 10, 1, 17, 24, 59)).total_seconds()
        domb_total_time = (datetime(2016, 10, 1, 18, 0, 0) - datetime(2016, 10, 1, 15, 30, 0)).total_seconds()

        domb_expected_availability = domb_available_time / domb_total_time
        self.assertAlmostEqual(domb_expected_availability, telescope_availability[self.tk2][0][1])

    @patch('valhalla.common.telescope_states.get_site_rise_set_intervals')
    def test_telescope_availability_spans_interval(self, mock_intervals):
        mock_intervals.return_value = [(datetime(2016, 9, 30, 15, 30, 0, tzinfo=timezone.utc),
                                        datetime(2016, 9, 30, 18, 0, 0, tzinfo=timezone.utc)),
                                       (datetime(2016, 10, 1, 15, 30, 0, tzinfo=timezone.utc),
                                        datetime(2016, 10, 1, 16, 0, 0, tzinfo=timezone.utc)),
                                       (datetime(2016, 10, 1, 16, 10, 0, tzinfo=timezone.utc),
                                        datetime(2016, 10, 1, 16, 20, 0, tzinfo=timezone.utc)),
                                       (datetime(2016, 10, 2, 15, 30, 0, tzinfo=timezone.utc),
                                        datetime(2016, 10, 2, 18, 0, 0, tzinfo=timezone.utc))]
        start = datetime(2016, 9, 30, tzinfo=timezone.utc)
        end = datetime(2016, 10, 2, tzinfo=timezone.utc)
        telescope_availability = get_telescope_availability_per_day(start, end)

        self.assertIn(self.tk1, telescope_availability)
        self.assertIn(self.tk2, telescope_availability)

        doma_available_time = (datetime(2016, 10, 1, 16, 0, 0) - datetime(2016, 10, 1, 15, 30, 0)).total_seconds()
        doma_available_time += (datetime(2016, 10, 1, 16, 20, 0) - datetime(2016, 10, 1, 16, 10, 0)).total_seconds()
        doma_total_time = doma_available_time

        doma_expected_availability = doma_available_time / doma_total_time
        self.assertAlmostEqual(doma_expected_availability, telescope_availability[self.tk1][0][1])

        domb_expected_availability = 1.0
        self.assertAlmostEqual(domb_expected_availability, telescope_availability[self.tk2][0][1])


class TelescopeStatesFromFile(TestCase):
    def setUp(self):
        self.configdb_null_patcher = patch('valhalla.common.configdb.ConfigDB._get_configdb_data')
        mock_configdb_null = self.configdb_null_patcher.start()
        mock_configdb_null.return_value = {}
        self.configdb_patcher = patch('valhalla.common.configdb.ConfigDB.get_instrument_types_per_telescope')
        self.mock_configdb = self.configdb_patcher.start()
        self.mock_configdb.return_value = {
            TelescopeKey(site='coj', observatory='clma', telescope='2m0a'): ['2M0-FLOYDS-SCICAM',
                                                                             '2M0-SCICAM-SPECTRAL'],
            TelescopeKey(site='coj', observatory='doma', telescope='1m0a'): ['1M0-SCICAM-SINISTRO'],
            TelescopeKey(site='coj', observatory='domb', telescope='1m0a'): ['1M0-SCICAM-SINISTRO'],
            TelescopeKey(site='cpt', observatory='domb', telescope='1m0a'): ['1M0-SCICAM-SINISTRO'],
            TelescopeKey(site='cpt', observatory='domc', telescope='1m0a'): ['1M0-SCICAM-SINISTRO'],
            TelescopeKey(site='elp', observatory='doma', telescope='1m0a'): ['1M0-SCICAM-SINISTRO'],
            TelescopeKey(site='lsc', observatory='domb', telescope='1m0a'): ['1M0-SCICAM-SINISTRO'],
            TelescopeKey(site='lsc', observatory='domc', telescope='1m0a'): ['1M0-SCICAM-SINISTRO'],
            TelescopeKey(site='ogg', observatory='clma', telescope='0m4b'): ['0M4-SCICAM-SBIG'],
            TelescopeKey(site='ogg', observatory='clma', telescope='2m0a'): ['2M0-FLOYDS-SCICAM'],
            TelescopeKey(site='sqa', observatory='doma', telescope='0m8a'): ['0M8-SCICAM-SBIG',
                                                                             '0M8-NRES-SCICAM']}

        with open('valhalla/common/test_data/es_telescope_states_data.txt', 'r') as input_file:
            self.es_output = json.loads(input_file.read())

        self.start = datetime(2016, 10, 1, tzinfo=timezone.utc)
        self.end = datetime(2016, 10, 10, tzinfo=timezone.utc)
        self.short_end = datetime(2016, 10, 4, tzinfo=timezone.utc)

        self.es_patcher = patch('valhalla.common.telescope_states.get_es_data')
        self.mock_es = self.es_patcher.start()
        self.mock_es.return_value = self.es_output

    def tearDown(self):
        self.configdb_patcher.stop()
        self.configdb_null_patcher.stop()
        self.es_patcher.stop()


class TestTelescopeStatesFromFile(TelescopeStatesFromFile):
    def test_one_telescope_correctness(self):
        telescope_states = get_telescope_states(self.start, self.end)
        tak = TelescopeKey(site='lsc', observatory='domb', telescope='1m0a')
        expected_events = [{'end': datetime(2016, 10, 3, 10, 25, 5, tzinfo=timezone.utc),
                            'event_reason': 'Available for scheduling',
                            'event_type': 'AVAILABLE',
                            'start': datetime(2016, 10, 1, 0, 0, 11, tzinfo=timezone.utc),
                            'telescope': 'lsc.domb.1m0a'},
                           {'end': datetime(2016, 10, 3, 10, 31, 20, tzinfo=timezone.utc),
                            'event_reason': 'Sequencer unavailable for scheduling',
                            'event_type': 'SEQUENCER_UNAVAILABLE',
                            'start': datetime(2016, 10, 3, 10, 25, 5, tzinfo=timezone.utc),
                            'telescope': 'lsc.domb.1m0a'},
                           {'end': datetime(2016, 10, 3, 16, 47, 42, tzinfo=timezone.utc),
                            'event_reason': 'Available for scheduling',
                            'event_type': 'AVAILABLE',
                            'start': datetime(2016, 10, 3, 10, 31, 20, tzinfo=timezone.utc),
                            'telescope': 'lsc.domb.1m0a'},
                           {'end': datetime(2016, 10, 3, 17, 7, 49, tzinfo=timezone.utc),
                            'event_reason': 'No update since 2016-10-03T16:37:35',
                            'event_type': 'SITE_AGENT_UNRESPONSIVE',
                            'start': datetime(2016, 10, 3, 16, 47, 42, tzinfo=timezone.utc),
                            'telescope': 'lsc.domb.1m0a'},
                           {'end': datetime(2016, 10, 3, 23, 35, 58, tzinfo=timezone.utc),
                            'event_reason': 'Available for scheduling',
                            'event_type': 'AVAILABLE',
                            'start': datetime(2016, 10, 3, 17, 7, 49, tzinfo=timezone.utc),
                            'telescope': 'lsc.domb.1m0a'},
                           {'end': datetime(2016, 10, 4, 1, 3, tzinfo=timezone.utc),
                            'event_reason': 'Sky transparency too low',
                            'event_type': 'NOT_OK_TO_OPEN',
                            'start': datetime(2016, 10, 3, 23, 35, 58, tzinfo=timezone.utc),
                            'telescope': 'lsc.domb.1m0a'},
                           {'end': datetime(2016, 10, 4, 1, 20, 46, tzinfo=timezone.utc),
                            'event_reason': 'Available for scheduling',
                            'event_type': 'AVAILABLE',
                            'start': datetime(2016, 10, 4, 1, 3, tzinfo=timezone.utc),
                            'telescope': 'lsc.domb.1m0a'},
                           {'end': datetime(2016, 10, 4, 1, 20, 47, tzinfo=timezone.utc),
                            'event_reason': 'Sky transparency too low',
                            'event_type': 'NOT_OK_TO_OPEN',
                            'start': datetime(2016, 10, 4, 1, 20, 46, tzinfo=timezone.utc),
                            'telescope': 'lsc.domb.1m0a'},
                           {'end': datetime(2016, 10, 4, 1, 26, 56, tzinfo=timezone.utc),
                            'event_reason': 'Sequencer unavailable for scheduling',
                            'event_type': 'SEQUENCER_UNAVAILABLE',
                            'start': datetime(2016, 10, 4, 1, 20, 47, tzinfo=timezone.utc),
                            'telescope': 'lsc.domb.1m0a'},
                           {'end': datetime(2016, 10, 4, 10, 24, 18, tzinfo=timezone.utc),
                            'event_reason': 'Sky transparency too low',
                            'event_type': 'NOT_OK_TO_OPEN',
                            'start': datetime(2016, 10, 4, 1, 26, 56, tzinfo=timezone.utc),
                            'telescope': 'lsc.domb.1m0a'},
                           {'end': datetime(2016, 10, 4, 10, 30, 55, tzinfo=timezone.utc),
                            'event_reason': 'Sequencer unavailable for scheduling',
                            'event_type': 'SEQUENCER_UNAVAILABLE',
                            'start': datetime(2016, 10, 4, 10, 24, 18, tzinfo=timezone.utc),
                            'telescope': 'lsc.domb.1m0a'},
                           {'end': datetime(2016, 10, 4, 21, 47, 6, tzinfo=timezone.utc),
                            'event_reason': 'Available for scheduling',
                            'event_type': 'AVAILABLE',
                            'start': datetime(2016, 10, 4, 10, 30, 55, tzinfo=timezone.utc),
                            'telescope': 'lsc.domb.1m0a'},
                           {'end': datetime(2016, 10, 5, 0, 58, 26, tzinfo=timezone.utc),
                            'event_reason': 'Sequencer in MANUAL state',
                            'event_type': 'SEQUENCER_DISABLED',
                            'start': datetime(2016, 10, 4, 21, 47, 6, tzinfo=timezone.utc),
                            'telescope': 'lsc.domb.1m0a'},
                           {'end': datetime(2016, 10, 6, 16, 48, 6, tzinfo=timezone.utc),
                            'event_reason': 'Available for scheduling',
                            'event_type': 'AVAILABLE',
                            'start': datetime(2016, 10, 5, 0, 58, 26, tzinfo=timezone.utc),
                            'telescope': 'lsc.domb.1m0a'},
                           {'end': datetime(2016, 10, 6, 16, 57, 19, tzinfo=timezone.utc),
                            'event_reason': 'No update since 2016-10-06T16:12:10',
                            'event_type': 'SITE_AGENT_UNRESPONSIVE',
                            'start': datetime(2016, 10, 6, 16, 48, 6, tzinfo=timezone.utc),
                            'telescope': 'lsc.domb.1m0a'},
                           {'end': datetime(2016, 10, 7, 10, 20, 44, tzinfo=timezone.utc),
                            'event_reason': 'Available for scheduling',
                            'event_type': 'AVAILABLE',
                            'start': datetime(2016, 10, 6, 16, 57, 19, tzinfo=timezone.utc),
                            'telescope': 'lsc.domb.1m0a'},
                           {'end': datetime(2016, 10, 7, 10, 28, 58, tzinfo=timezone.utc),
                            'event_reason': 'Sequencer unavailable for scheduling',
                            'event_type': 'SEQUENCER_UNAVAILABLE',
                            'start': datetime(2016, 10, 7, 10, 20, 44, tzinfo=timezone.utc),
                            'telescope': 'lsc.domb.1m0a'},
                           {'end': datetime(2016, 10, 8, 10, 20, 25, tzinfo=timezone.utc),
                            'event_reason': 'Available for scheduling',
                            'event_type': 'AVAILABLE',
                            'start': datetime(2016, 10, 7, 10, 28, 58, tzinfo=timezone.utc),
                            'telescope': 'lsc.domb.1m0a'},
                           {'end': datetime(2016, 10, 8, 10, 28, 36, tzinfo=timezone.utc),
                            'event_reason': 'Sequencer unavailable for scheduling',
                            'event_type': 'SEQUENCER_UNAVAILABLE',
                            'start': datetime(2016, 10, 8, 10, 20, 25, tzinfo=timezone.utc),
                            'telescope': 'lsc.domb.1m0a'},
                           {'end': datetime(2016, 10, 10, 0, 0, tzinfo=timezone.utc),
                            'event_reason': 'Available for scheduling',
                            'event_type': 'AVAILABLE',
                            'start': datetime(2016, 10, 8, 10, 28, 36, tzinfo=timezone.utc),
                            'telescope': 'lsc.domb.1m0a'}]
        # looked in depth at lsc.domb.1m0a in the date range to verify correctness of this
        # data is available on the telescope_events index of elasticsearch
        self.assertEqual(telescope_states[tak], expected_events)

    def test_states_no_enclosure_interlock(self):
        telescope_states = get_telescope_states(self.start, self.end)

        self.assertNotIn("ENCLOSURE_INTERLOCK", telescope_states)

    def test_states_end_time_after_start(self):
        telescope_states = get_telescope_states(self.start, self.end)

        for tk, events in telescope_states.items():
            for event in events:
                self.assertTrue(event['start'] <= event['end'])

    def test_states_no_duplicate_consecutive_states(self):
        telescope_states = get_telescope_states(self.start, self.end)

        for tk, events in telescope_states.items():
            previous_event = None
            for event in events:
                if previous_event:
                    self.assertTrue(previous_event['event_type'] != event['event_type'] or
                                    previous_event['event_reason'] != event['event_reason'])
                previous_event = event
