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

        tk1 = TelescopeKey('tst', 'doma', '1m0a')
        tk2 = TelescopeKey('tst', 'domb', '1m0a')

        self.assertIn(tk1, telescope_states)
        self.assertIn(tk2, telescope_states)

        doma_expected_available_state = {'telescope': 'tst.doma.1m0a',
                                         'event_type': 'AVAILABLE',
                                         'event_reason': 'Available for scheduling',
                                         'start': datetime(2016, 10, 1, 15, 24, 58),
                                         'end': datetime(2016, 10, 1, 17, 44, 58)
                                         }

        self.assertIn(doma_expected_available_state, telescope_states[tk1])

