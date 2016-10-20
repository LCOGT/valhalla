from django.conf import settings
from elasticsearch import Elasticsearch
from datetime import datetime, timedelta
from copy import deepcopy
import logging

from valhalla.common.configdb import ConfigDB, TelescopeKey
from valhalla.common.rise_set_utils import get_site_rise_set_intervals

logger = logging.getLogger(__name__)

ES_STRING_FORMATTER = "%Y-%m-%d %H:%M:%S"


def get_telescope_states(start, end, telescopes=None, sites=None, instrument_types=None):
    configdb = ConfigDB()
    telescope_to_instruments = configdb.get_instrument_types_per_telescope()
    if not instrument_types:
        available_telescopes = telescope_to_instruments.keys()
    else:
        available_telescopes = [tk for tk, insts in telescope_to_instruments.items() if
                                any(inst in insts for inst in instrument_types)]

    if not sites:
        sites = list(set([telescope_key.site for telescope_key in available_telescopes]))

    if not telescopes:
        telescopes = list(set([tk.telescope for tk in available_telescopes if tk.site in sites]))

    es = Elasticsearch([settings.ELASTICSEARCH_URL])

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

    data = es.search(index="telescope_events", body=date_range_query, size=10000,
                     _source=['timestamp', 'telescope', 'enclosure', 'site', 'type', 'reason'], sort=['timestamp'])

    telescope_status = {}
    last_event = {}

    for events in data['hits']['hits']:
        # ignore the enclosure_interlock state as it is redundant
        if events['_source']['type'].upper() == 'ENCLOSURE_INTERLOCK':
            continue
        telescope_key = TelescopeKey(site=events['_source']['site'],
                                     observatory=events['_source']['enclosure'],
                                     telescope=events['_source']['telescope'])
        if telescope_key in available_telescopes:
            timestamp = datetime.strptime(events['_source']['timestamp'], ES_STRING_FORMATTER)
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
                                                             ES_STRING_FORMATTER),
                                                         'end': timestamp})
                last_event[telescope_key] = events['_source']

    for telescope_key, event in last_event.items():
        if event:
            telescope_status[telescope_key].append({'telescope': str(telescope_key),
                                                     'event_type': event['type'],
                                                     'event_reason': event['reason'],
                                                     'start': datetime.strptime(event['timestamp'],
                                                                                ES_STRING_FORMATTER),
                                                     'end': end})

    return telescope_status


def filter_telescope_states_by_intervals(telescope_states, sites_intervals):
    filtered_states = {}
    for telescope_key, events in telescope_states.items():
        # now loop through the events for the telescope, and tally the time the telescope is available for each 'day'
        site_intervals = sites_intervals[telescope_key.site]
        filtered_events = []

        for event in events:
            for interval in site_intervals:
                if event['start'] >= interval[0] and event['end'] <= interval[1]:
                    # the event is fully contained to add it and break out
                    filtered_events.append(deepcopy(event))
                elif event['start'] < interval[0] and event['end'] > interval[1]:
                    # start is before interval and end is after, so it spans the interval
                    extra_event = deepcopy(event)
                    extra_event['start'] = interval[0]
                    extra_event['end'] = interval[1]
                    filtered_events.append(deepcopy(extra_event))
                elif event['start'] < interval[0] and event['end'] > interval[0] and event['end'] <= interval[1]:
                    # start is before interval and end is in interval, so truncate start
                    extra_event = deepcopy(event)
                    extra_event['start'] = interval[0]
                    filtered_events.append(deepcopy(extra_event))
                elif event['start'] >= interval[0] and event['start'] < interval[1] and event['end'] > interval[1]:
                    # start is within interval and end is after, so truncate end
                    extra_event = deepcopy(event)
                    extra_event['end'] = interval[1]
                    filtered_events.append(deepcopy(extra_event))

        filtered_states[telescope_key] = filtered_events

    return filtered_states


def get_telescope_availability_per_day(start, end, telescope_classes=None, sites=None, instrument_types=None):
    telescope_states = get_telescope_states(start, end, telescope_classes, sites, instrument_types)
    # go through each telescopes list of states, grouping it up by observing night at the site
    rise_set_intervals = {}
    for telescope_key, events in telescope_states.items():
        if telescope_key.site not in rise_set_intervals:
            # remove the first and last interval as they may only be partial intervals
            rise_set_intervals[telescope_key.site] = get_site_rise_set_intervals(start, end, telescope_key.site)[1:-1]
    filtered_events = filter_telescope_states_by_intervals(telescope_states, rise_set_intervals)
    # now just compute a % available each day from the rise_set filtered set of events
    telescope_availability = {}
    for telescope_key, events in filtered_events.items():
        telescope_availability[telescope_key] = []
        time_available = timedelta(seconds=0)
        time_total = timedelta(seconds=0)
        if events:
            current_day = list(events)[0]['start'].date()
            current_end = list(events)[0]['start']
        for event in events:
            if (event['start'] - current_end) > timedelta(hours=4):
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
