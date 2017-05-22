from django.conf import settings
from elasticsearch import Elasticsearch
from datetime import datetime, timedelta
from django.utils import timezone
from copy import deepcopy
from urllib3.exceptions import LocationValueError
from django.core.exceptions import ImproperlyConfigured
import logging

from valhalla.common.configdb import configdb, TelescopeKey
from valhalla.common.rise_set_utils import get_site_rise_set_intervals

logger = logging.getLogger(__name__)

ES_STRING_FORMATTER = "%Y-%m-%d %H:%M:%S"


def string_to_datetime(timestamp, time_format=ES_STRING_FORMATTER):
    return datetime.strptime(timestamp, time_format).replace(tzinfo=timezone.utc)


class TelescopeStates(object):
    def __init__(self, start, end, telescopes=None, sites=None, instrument_types=None):
        try:
            self.es = Elasticsearch([settings.ELASTICSEARCH_URL])
        except LocationValueError:
            logger.error('Could not find host. Make sure ELASTICSEARCH_URL is set.')
            raise ImproperlyConfigured('ELASTICSEARCH_URL')

        self.instrument_types = instrument_types
        self.available_telescopes = self._get_available_telescopes()

        sites = list({tk.site for tk in self.available_telescopes}) if not sites else sites
        telescopes = list({tk.telescope for tk in self.available_telescopes if tk.site in sites}) \
            if not telescopes else telescopes

        self.start = start.replace(tzinfo=timezone.utc).replace(microsecond=0)
        self.end = end.replace(tzinfo=timezone.utc).replace(microsecond=0)
        self.event_data = self._get_es_data(sites, telescopes)

    def _get_available_telescopes(self):
        telescope_to_instruments = configdb.get_instrument_types_per_telescope(only_schedulable=True)
        if not self.instrument_types:
            available_telescopes = telescope_to_instruments.keys()
        else:
            available_telescopes = [tk for tk, insts in telescope_to_instruments.items() if
                                    any(inst in insts for inst in self.instrument_types)]
        return available_telescopes

    def _get_es_data(self, sites, telescopes):
        date_range_query = {
            "query": {
                "filtered": {
                    "filter": {
                        "and": [
                            {
                                "range": {
                                    "timestamp": {
                                        # Retrieve documents 1 hour back to capture the telescope state at the start.
                                        "gte": (self.start - timedelta(hours=1)).strftime(ES_STRING_FORMATTER),
                                        "lte": self.end.strftime(ES_STRING_FORMATTER),
                                        "format": "yyyy-MM-dd HH:mm:ss"
                                    }
                                }
                            },
                            {
                                "terms": {
                                    "telescope": telescopes
                                }
                            },
                            {
                                "terms": {
                                    "site": sites
                                }
                            }
                        ]
                    }
                }
            }
        }
        event_data = []
        query_size = 10000
        data = self.es.search(index="telescope_events", body=date_range_query, size=query_size, scroll='1m',
                              _source=['timestamp', 'telescope', 'enclosure', 'site', 'type', 'reason'],
                              sort=['site', 'enclosure', 'telescope', 'timestamp'])  # noqa
        event_data.extend(data['hits']['hits'])
        total_events = data['hits']['total']
        events_read = min(query_size, total_events)
        scroll_id = data.get('_scroll_id', 0)
        while events_read < total_events:
            data = self.es.scroll(scroll_id=scroll_id, scroll='1m') # noqa
            scroll_id = data.get('_scroll_id', 0)
            event_data.extend(data['hits']['hits'])
            events_read += len(data['hits']['hits'])
        return event_data

    def _belongs_in_lump(self, event_source, lump_data, dt=60):
        if str(lump_data['telescope']) != str(self._telescope(event_source)):
            return False

        time_diff = (string_to_datetime(event_source['timestamp']) - lump_data['latest_timestamp']).total_seconds()

        # If the event is close enough to the latest timestamp in the lump, it belongs in that lump.
        if time_diff < dt:
            return True

        # If the event is far in time from the lump, but has the same reason, that means it came from the same
        # scheduling run as that timestamp and belongs in the lump.
        if time_diff >= dt and event_source['reason'] in lump_data['reasons']:
            return True

        # If the event is an ENCLOSURE_INTERLOCK, and the lump includes a SEQUENCER_UNAVAILABLE, it is part of the
        # lump. This is because the two states are redundant.
        if event_source['type'] == 'ENCLOSURE_INTERLOCK' and 'SEQUENCER_UNAVAILABLE' in lump_data['types']:
            return True

        return False

    @staticmethod
    def _categorize(lump):
        # TODO: Categorize each lump in a useful way for network users.
        event_type, event_reason = lump['types'][0], lump['reasons'][0]
        for this_type, this_reason in zip(lump['types'], lump['reasons']):
            # If the state in ENCLOSURE INTERLOCK, wait to instead categorize as SEQUENCER_UNAVAILABLE.
            if this_type.upper() != 'ENCLOSURE_INTERLOCK':
                event_type, event_reason = this_type, this_reason
                break
        return event_type, event_reason

    def _lump_end(self, lump, next_event=None):
        if not next_event or str(lump['telescope']) != str(self._telescope(next_event)):
            return self.end
        return string_to_datetime(next_event['timestamp'])

    def _set_lump(self, event):
        return {
            'reasons': [event['_source']['reason']],
            'types': [event['_source']['type']],
            'start': string_to_datetime(event['_source']['timestamp']),
            'telescope': self._telescope(event['_source']),
            'latest_timestamp': string_to_datetime(event['_source']['timestamp'])
        }

    @staticmethod
    def _update_lump(lump, event):
        if event['_source']['type'] not in lump['types'] or event['_source']['reason'] not in lump['reasons']:
            lump['reasons'].append(event['_source']['reason'])
            lump['types'].append(event['_source']['type'])
        lump['latest_timestamp'] = string_to_datetime(event['_source']['timestamp'])
        return lump

    def get(self):
        telescope_states = {}
        current_lump = dict(reasons=None, types=None, start=None)

        for event in self.event_data:
            if self._telescope(event['_source']) not in self.available_telescopes:
                continue

            if current_lump['start'] is None:
                current_lump = self._set_lump(event)
                continue

            if self._belongs_in_lump(event['_source'], current_lump):
                current_lump = self._update_lump(current_lump, event)
            else:
                lump_end = self._lump_end(current_lump, event['_source'])
                if lump_end >= self.start:
                    telescope_states = self._update_states(telescope_states, current_lump, lump_end)
                    current_lump = self._set_lump(event)

        if current_lump['start']:
            lump_end = self._lump_end(current_lump)
            telescope_states = self._update_states(telescope_states, current_lump, lump_end)

        return telescope_states

    def _update_states(self, states, lump, lump_end):
        if lump['telescope'] not in states:
            states[lump['telescope']] = []

        event_type, event_reason = self._categorize(lump)
        states[lump['telescope']].append(
            {
                'telescope': str(lump['telescope']),
                'event_type': event_type,
                'event_reason': event_reason,
                'start': max(self.start, lump['start']),
                'end': lump_end
            }
        )
        return states

    @staticmethod
    def _telescope(event_source):
        return TelescopeKey(
            site=event_source['site'],
            observatory=event_source['enclosure'],
            telescope=event_source['telescope']
        )


def filter_telescope_states_by_intervals(telescope_states, sites_intervals, start, end):
    filtered_states = {}
    for telescope_key, events in telescope_states.items():
        # now loop through the events for the telescope, and tally the time the telescope is available for each 'day'
        if telescope_key.site in sites_intervals:
            site_intervals = sites_intervals[telescope_key.site]
            filtered_events = []

            for event in events:
                event_start = max(event['start'], start)
                event_end = min(event['end'], end)
                for interval in site_intervals:
                    if event_start >= interval[0] and event_end <= interval[1]:
                        # the event is fully contained to add it and break out
                        extra_event = deepcopy(event)
                        extra_event['start'] = event_start
                        extra_event['end'] = event_end
                        filtered_events.append(deepcopy(event))
                    elif event_start < interval[0] and event_end > interval[1]:
                        # start is before interval and end is after, so it spans the interval
                        extra_event = deepcopy(event)
                        extra_event['start'] = interval[0]
                        extra_event['end'] = interval[1]
                        filtered_events.append(deepcopy(extra_event))
                    elif event_start < interval[0] and event_end > interval[0] and event_end <= interval[1]:
                        # start is before interval and end is in interval, so truncate start
                        extra_event = deepcopy(event)
                        extra_event['start'] = interval[0]
                        extra_event['end'] = event_end
                        filtered_events.append(deepcopy(extra_event))
                    elif event_start >= interval[0] and event_start < interval[1] and event_end > interval[1]:
                        # start is within interval and end is after, so truncate end
                        extra_event = deepcopy(event)
                        extra_event['start'] = event_start
                        extra_event['end'] = interval[1]
                        filtered_events.append(deepcopy(extra_event))

            filtered_states[telescope_key] = filtered_events

    return filtered_states


def get_telescope_availability_per_day(start, end, telescopes=None, sites=None, instrument_types=None):
    telescope_states = TelescopeStates(start, end, telescopes, sites, instrument_types).get()
    # go through each telescopes list of states, grouping it up by observing night at the site
    rise_set_intervals = {}
    for telescope_key, events in telescope_states.items():
        if telescope_key.site not in rise_set_intervals:
            # remove the first and last interval as they may only be partial intervals
            rise_set_intervals[telescope_key.site] = get_site_rise_set_intervals(start - timedelta(days=1),
                                                                                 end + timedelta(days=1),
                                                                                 telescope_key.site)[1:]
    telescope_states = filter_telescope_states_by_intervals(telescope_states, rise_set_intervals, start, end)
    # now just compute a % available each day from the rise_set filtered set of events
    telescope_availability = {}
    for telescope_key, events in telescope_states.items():
        telescope_availability[telescope_key] = []
        time_available = timedelta(seconds=0)
        time_total = timedelta(seconds=0)
        if events:
            current_day = list(events)[0]['start'].date()
            current_end = list(events)[0]['start']
        for event in events:
            if (event['start'] - current_end) > timedelta(hours=4):
                if (event['start'].date() != current_day):
                    # we must be in a new observing day, so tally time in previous day and increment day counter
                    telescope_availability[telescope_key].append([current_day, (
                        time_available.total_seconds() / time_total.total_seconds())])
                time_available = timedelta(seconds=0)
                time_total = timedelta(seconds=0)
                current_day = event['start'].date()

            if 'AVAILABLE' == event['event_type'].upper():
                time_available += event['end'] - event['start']
            time_total += event['end'] - event['start']
            current_end = event['end']

        if time_total > timedelta():
            telescope_availability[telescope_key].append([current_day, (
                time_available.total_seconds() / time_total.total_seconds())])

    return telescope_availability


def combine_telescope_availabilities_by_site_and_class(telescope_availabilities):
    combined_keys = {TelescopeKey(tk.site, '', tk.telescope[:-1]) for tk in telescope_availabilities.keys()}
    combined_availabilities = {}
    for key in combined_keys:
        num_groups = 0
        total_availability = []
        for telescope_key, availabilities in telescope_availabilities.items():
            if telescope_key.site == key.site and telescope_key.telescope[:-1] == key.telescope:
                num_groups += 1
                if not total_availability:
                    total_availability = availabilities
                else:
                    for i, availability in enumerate(availabilities):
                        total_availability[i][1] += availability[1]

        for i, availability in enumerate(total_availability):
            total_availability[i][1] /= num_groups
        combined_availabilities[key] = total_availability

    return combined_availabilities
