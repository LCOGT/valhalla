from valhalla.userrequests.duration_utils import get_request_duration
from valhalla.common.rise_set_utils import get_rise_set_intervals, get_largest_interval

from rest_framework.exceptions import APIException

from datetime import timedelta


class InvalidCadenceException(APIException):
    status_code = 400 # Bad Request
    default_detail = 'Invalid Cadence Request'
    default_code = 'invalid_request'


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
        window_dict = {'start': window_start, 'end': window_end}

        # test the rise_set of this window
        request_dict['windows'] = [window_dict]
        intervals = get_rise_set_intervals(request_dict)
        largest_interval = get_largest_interval(intervals)
        if largest_interval.total_seconds() >= request_duration:
            # this cadence window passes rise_set, so add it to the list
            request_copy = request_dict.copy()
            del request_copy['cadence']
            # request_copy['molecules'] = request_copy['molecule_set']
            # del request_copy['molecule_set']
            cadence_requests.append(request_copy)

        request_window_start += timedelta(hours=cadence['period'])

    return cadence_requests

