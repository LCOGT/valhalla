from valhalla.common.telescope_states import get_telescope_states, get_telescope_availability_per_day
from valhalla.common.test_configdb import configdb_data
from valhalla.common.configdb import TelescopeKey

from unittest.case import TestCase
from datetime import datetime
from unittest.mock import patch, MagicMock


class TestTelescopeStates(TestCase):
    def setUp(self):
        self.configdb_patcher = patch('valhalla.common.configdb.ConfigDB._get_configdb_data')
        self.mock_configdb = self.configdb_patcher.start()
        self.mock_configdb.return_value = configdb_data

        self.es_output_1 = {
            'hits': {
                'hits': [
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
            }
        }

        self.tk1 = TelescopeKey('tst', 'doma', '1m0a')
        self.tk2 = TelescopeKey('tst', 'domb', '1m0a')

        self.es_patcher = patch('valhalla.common.telescope_states.Elasticsearch')
        self.mock_es = self.es_patcher.start()
        self.mock_es_search = MagicMock(search=MagicMock(return_value=self.es_output_1))
        self.mock_es.return_value = self.mock_es_search

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
                                         'start': datetime(2016, 10, 1, 15, 24, 58),
                                         'end': datetime(2016, 10, 1, 17, 44, 58)
                                         }

        self.assertIn(doma_expected_available_state, telescope_states[self.tk1])

        domb_expected_available_state1 = {'telescope': 'tst.domb.1m0a',
                                          'event_type': 'AVAILABLE',
                                          'event_reason': 'Available for scheduling',
                                          'start': datetime(2016, 10, 1, 15, 30, 0),
                                          'end': datetime(2016, 10, 1, 16, 24, 59)
                                          }

        self.assertIn(domb_expected_available_state1, telescope_states[self.tk2])

        domb_expected_available_state2 = {'telescope': 'tst.domb.1m0a',
                                          'event_type': 'AVAILABLE',
                                          'event_reason': 'Available for scheduling',
                                          'start': datetime(2016, 10, 1, 17, 24, 59),
                                          'end': datetime(2016, 10, 1, 17, 44, 58)
                                          }
        self.assertIn(domb_expected_available_state2, telescope_states[self.tk2])

    def test_aggregate_states_no_enclosure_interlock(self):
        start = datetime(2016, 10, 1)
        end = datetime(2016, 10, 2)
        telescope_states = get_telescope_states(start, end)

        self.assertIn(self.tk1, telescope_states)
        self.assertIn(self.tk2, telescope_states)
        self.assertNotIn("ENCLOSURE_INTERLOCK", telescope_states)

    @patch('valhalla.common.telescope_states.get_site_rise_set_intervals')
    def test_telescope_availability(self, mock_intervals):
        mock_intervals.return_value = [(datetime(2016, 9, 30, 15, 30, 0), datetime(2016, 9, 30, 18, 0, 0)),
                                       (datetime(2016, 10, 1, 15, 30, 0), datetime(2016, 10, 1, 18, 0, 0)),
                                       (datetime(2016, 10, 2, 15, 30, 0), datetime(2016, 10, 2, 18, 0, 0))]
        start = datetime(2016, 9, 30)
        end = datetime(2016, 10, 2)
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
        mock_intervals.return_value = [(datetime(2016, 9, 30, 15, 30, 0), datetime(2016, 9, 30, 18, 0, 0)),
                                       (datetime(2016, 10, 1, 15, 30, 0), datetime(2016, 10, 1, 16, 0, 0)),
                                       (datetime(2016, 10, 1, 16, 10, 0), datetime(2016, 10, 1, 16, 20, 0)),
                                       (datetime(2016, 10, 2, 15, 30, 0), datetime(2016, 10, 2, 18, 0, 0))]
        start = datetime(2016, 9, 30)
        end = datetime(2016, 10, 2)
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
