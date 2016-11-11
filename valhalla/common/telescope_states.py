from django.conf import settings
from elasticsearch import Elasticsearch
from datetime import datetime, timedelta
from django.utils import timezone
from copy import deepcopy
from urllib3.exceptions import LocationValueError
from django.core.exceptions import ImproperlyConfigured
import logging

from valhalla.common.configdb import ConfigDB, TelescopeKey
from valhalla.common.rise_set_utils import get_site_rise_set_intervals

logger = logging.getLogger(__name__)

ES_STRING_FORMATTER = "%Y-%m-%d %H:%M:%S"


def get_es_data(query):
    try:
        es = Elasticsearch([settings.ELASTICSEARCH_URL])
    except LocationValueError:
        logger.error('Could not find host. Make sure ELASTICSEARCH_URL is set.')
        raise ImproperlyConfigured('ELASTICSEARCH_URL')

    event_data = []
    query_size = 10000
    data = es.search(index="telescope_events", body=query, size=query_size, scroll='1m',
                     _source=['timestamp', 'telescope', 'enclosure', 'site', 'type', 'reason'], sort=['timestamp'])
    event_data.extend(data['hits']['hits'])
    total_events = data['hits']['total']
    events_read = min(query_size, total_events)
    scroll_id = data.get('_scroll_id', 0)
    while events_read < total_events:
        data = es.scroll(scroll_id=scroll_id, scroll='1m')
        scroll_id = data.get('_scroll_id', 0)
        event_data.extend(data['hits']['hits'])
        events_read += len(data['hits']['hits'])

    return event_data


def get_telescope_states(start, end, telescopes=None, sites=None, instrument_types=None):
    telescope_to_instruments = ConfigDB().get_instrument_types_per_telescope()
    if not instrument_types:
        available_telescopes = telescope_to_instruments.keys()
    else:
        available_telescopes = [tk for tk, insts in telescope_to_instruments.items() if
                                any(inst in insts for inst in instrument_types)]

    if not sites:
        sites = list({telescope_key.site for telescope_key in available_telescopes})

    if not telescopes:
        telescopes = list({tk.telescope for tk in available_telescopes if tk.site in sites})

    date_range_query = {
        "query": {
            "filtered": {
                "filter": {
                    "and": [
                        {
                            "range": {
                                "timestamp": {
                                    "gte": start.strftime(ES_STRING_FORMATTER),
                                    "lte": end.strftime(ES_STRING_FORMATTER),
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

    event_data = get_es_data(date_range_query)
    telescope_status = {}
    last_event = {}

    for events in event_data:
        # ignore the enclosure_interlock state as it is redundant
        if events['_source']['type'].upper() == 'ENCLOSURE_INTERLOCK':
            continue
        telescope_key = TelescopeKey(site=events['_source']['site'],
                                     observatory=events['_source']['enclosure'],
                                     telescope=events['_source']['telescope'])
        if telescope_key in available_telescopes:
            timestamp = datetime.strptime(events['_source']['timestamp'],
                                          ES_STRING_FORMATTER).replace(tzinfo=timezone.utc)
            if telescope_key not in telescope_status:
                telescope_status[telescope_key] = []
                last_event[telescope_key] = None

            if not last_event[telescope_key]:
                last_event[telescope_key] = events['_source']
            elif (last_event[telescope_key]['type'] != events['_source']['type']
                  or last_event[telescope_key]['reason'] != events['_source']['reason']):
                telescope_status[telescope_key].append({'telescope': str(telescope_key),
                                                        'event_type': last_event[telescope_key]['type'],
                                                        'event_reason': last_event[telescope_key]['reason'],
                                                        'start': datetime.strptime(
                                                            last_event[telescope_key]['timestamp'],
                                                            ES_STRING_FORMATTER).replace(tzinfo=timezone.utc),
                                                        'end': timestamp})
                last_event[telescope_key] = events['_source']

    for telescope_key, event in last_event.items():
        if event:
            telescope_status[telescope_key].append({'telescope': str(telescope_key),
                                                    'event_type': event['type'],
                                                    'event_reason': event['reason'],
                                                    'start': datetime.strptime(event['timestamp'],
                                                                               ES_STRING_FORMATTER)
                                                    .replace(tzinfo=timezone.utc),
                                                    'end': end})

    return telescope_status


def filter_telescope_states_by_intervals(telescope_states, sites_intervals, start, end):
    filtered_states = {}
    for telescope_key, events in telescope_states.items():
        # now loop through the events for the telescope, and tally the time the telescope is available for each 'day'
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
    telescope_states = get_telescope_states(start, end, telescopes, sites, instrument_types)
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
