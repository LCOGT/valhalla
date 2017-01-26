from valhalla.userrequests.duration_utils import get_request_duration
from valhalla.common.rise_set_utils import get_rise_set_intervals, get_largest_interval

from datetime import timedelta


def get_cadence_requests(request_dict):
    cadence = request_dict['cadence']
    # now expand the request into a list of requests with the proper windows from the cadence block
    cadence_requests = []
    half_jitter = timedelta(hours=cadence['jitter'] / 2.0)
    request_duration = get_request_duration(request_dict)
    request_window_start = cadence['start']

    while request_window_start < cadence['end']:
        window_start = max(request_window_start - half_jitter, cadence['start'])
        window_end = min(request_window_start + half_jitter, cadence['end'])

        # test the rise_set of this window
        request_dict['windows'] = [{'start': window_start, 'end': window_end}]
        intervals = get_rise_set_intervals(request_dict)
        largest_interval = get_largest_interval(intervals)
        if largest_interval.total_seconds() >= request_duration:
            # this cadence window passes rise_set, so add it to the list
            request_copy = request_dict.copy()
            del request_copy['cadence']
            cadence_requests.append(request_copy)

        request_window_start += timedelta(hours=cadence['period'])
    return cadence_requests

