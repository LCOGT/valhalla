import itertools
from django.utils.translation import ugettext as _
from math import ceil

from valhalla.proposals.models import TimeAllocationKey, Proposal, Semester
from valhalla.common.configdb import configdb
from valhalla.common.rise_set_utils import get_rise_set_intervals, get_largest_interval

import logging
logger = logging.getLogger(__name__)


PER_MOLECULE_GAP = 5.0             # in-between molecule gap - shared for all instruments
PER_MOLECULE_STARTUP_TIME = 11.0   # per-molecule startup time, which encompasses filter changes
OVERHEAD_ALLOWANCE = 1.1           # amount of leeway in a proposals timeallocation before rejecting that request
MAX_IPP_LIMIT = 2.0                # the maximum allowed value of ipp
MIN_IPP_LIMIT = 0.5                # the minimum allowed value of ipp


semesters = None
def get_semesters():
    global semesters;
    if not semesters:
        semesters = list(Semester.objects.filter(public=True).order_by('-start').all())
    return semesters


def get_semester_in(start_date, end_date):
    semesters = get_semesters()
    for semester in semesters:
        if start_date >= semester.start and end_date <= semester.end:
            return semester

    return None


def get_num_mol_changes(molecules):
    return len(list(itertools.groupby([mol['type'].upper() for mol in molecules])))


def get_num_filter_changes(molecules):
    return len(list(itertools.groupby([mol.get('filter', '') for mol in molecules])))


def get_molecule_duration_per_exposure(molecule_dict):
    total_overhead_per_exp = configdb.get_exposure_overhead(molecule_dict['instrument_name'], molecule_dict['bin_x'])
    mol_duration_per_exp = molecule_dict['exposure_time'] + total_overhead_per_exp
    return mol_duration_per_exp


def get_molecule_duration(molecule_dict):
    mol_duration_per_exp = get_molecule_duration_per_exposure(molecule_dict)
    mol_duration = molecule_dict['exposure_count'] * mol_duration_per_exp
    duration = mol_duration + PER_MOLECULE_GAP + PER_MOLECULE_STARTUP_TIME

    return duration


def get_request_duration_dict(request_dict):
    req_durations = {'requests': []}
    for req in request_dict:
        req_info = {'duration': get_request_duration(req)}
        mol_durations = [{'duration': get_molecule_duration_per_exposure(mol)} for mol in req['molecules']]
        req_info['molecules'] = mol_durations
        req_info['largest_interval'] = get_largest_interval(get_rise_set_intervals(req)).total_seconds()
        req_info['largest_interval'] -= (PER_MOLECULE_STARTUP_TIME + PER_MOLECULE_GAP)
        req_durations['requests'].append(req_info)
    req_durations['duration'] = sum([req['duration'] for req in req_durations['requests']])

    return req_durations


def get_max_ipp_for_userrequest(userrequest_dict):
    proposal = Proposal.objects.get(pk=userrequest_dict['proposal'])
    request_durations = get_request_duration_sum(userrequest_dict)
    ipp_dict = {}
    for tak, duration in request_durations.items():
        time_allocation = proposal.timeallocation_set.get(semester=tak.semester, telescope_class=tak.telescope_class)
        duration_hours = duration / 3600.0
        ipp_available = time_allocation.ipp_time_available
        max_ipp_allowable = min((ipp_available / duration_hours) + 1.0, MAX_IPP_LIMIT)
        max_ipp_allowable = float("{:.3f}".format(max_ipp_allowable))
        if tak.semester not in ipp_dict:
            ipp_dict[tak.semester] = {}
        ipp_dict[tak.semester][tak.telescope_class] = {
            'ipp_time_available': ipp_available,
            'ipp_limit': time_allocation.ipp_limit,
            'request_duration': duration_hours,
            'max_allowable_ipp_value': max_ipp_allowable,
            'min_allowable_ipp_value': MIN_IPP_LIMIT
        }
    return ipp_dict


def get_request_duration_sum(userrequest_dict):
    duration_sum = {}
    for req in userrequest_dict['requests']:
        duration = get_request_duration(req)
        tak = get_time_allocation_key(
            telescope_class=req['location']['telescope_class'],
            min_window_time=min([w['start'] for w in req['windows']]),
            max_window_time=max([w['end'] for w in req['windows']])
        )
        if tak not in duration_sum:
            duration_sum[tak] = 0
        duration_sum[tak] += duration
    return duration_sum


def get_num_exposures(molecule_dict, time_available):
    mol_duration_per_exp = get_molecule_duration_per_exposure(molecule_dict)
    exposure_time = time_available.total_seconds() - PER_MOLECULE_GAP - PER_MOLECULE_STARTUP_TIME
    num_exposures = exposure_time // mol_duration_per_exp

    return max(1, num_exposures)


def get_request_duration(request_dict):
    # calculate the total time needed by the request, based on its instrument and exposures
    request_overheads = configdb.get_request_overheads(request_dict['molecules'][0]['instrument_name'])
    duration = sum([get_molecule_duration(m) for m in request_dict['molecules']])
    if configdb.is_spectrograph(request_dict['molecules'][0]['instrument_name']):
        duration += get_num_mol_changes(request_dict['molecules']) * request_overheads['config_change_time']

        if request_dict['target'].get('acquire_mode', '').upper() != 'OFF':
            mol_types = [mol['type'].upper() for mol in request_dict['molecules']]
            # Only add the overhead if we have on-sky targets to acquire
            if 'SPECTRUM' in mol_types or 'STANDARD' in mol_types:
                duration += request_overheads['acquire_exposure_time'] + \
                    request_overheads['acquire_processing_time']

    else:
        duration += get_num_filter_changes(request_dict['molecules']) * request_overheads['filter_change_time']

    duration += request_overheads['front_padding']
    duration = ceil(duration)

    return duration


def get_time_allocation(telescope_class, proposal_id, min_window_time, max_window_time):
    timeall = None
    try:
        timeall = Proposal.objects.get(pk=proposal_id).timeallocation_set.get(
            semester__start__lte=min_window_time,
            semester__end__gte=max_window_time,
            semester__public=True,
            telescope_class=telescope_class)
    except Exception:
        logger.warn(_("proposal {} has overlapping time allocations for {}").format(proposal_id, telescope_class))
    return timeall


def get_time_allocation_key(telescope_class, min_window_time, max_window_time):
    semester = get_semester_in(min_window_time, max_window_time)
    return TimeAllocationKey(semester.id, telescope_class)


def get_total_duration_dict(userrequest_dict):
    durations = []
    for request in userrequest_dict['requests']:
        min_window_time = min([window['start'] for window in request['windows']])
        max_window_time = max([window['end'] for window in request['windows']])
        tak = get_time_allocation_key(request['location']['telescope_class'],
                                      min_window_time,
                                      max_window_time
                                      )
        duration = get_request_duration(request)
        durations.append((tak, duration))
    # check the proposal has a time allocation with enough time for all requests depending on operator
    total_duration = {}
    if userrequest_dict['operator'] == 'SINGLE':
        (tak, duration) = durations[0]
        total_duration[tak] = duration

    elif userrequest_dict['operator'] in ['MANY', 'ONEOF']:
        for (tak, duration) in durations:
            total_duration[tak] = max(total_duration.get(tak, 0.0), duration)
    elif userrequest_dict['operator'] == 'AND':
        for (tak, duration) in durations:
            if tak not in total_duration:
                total_duration[tak] = 0
            total_duration[tak] += duration

    return total_duration
