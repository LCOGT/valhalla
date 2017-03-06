from valhalla.proposals.models import TimeAllocationKey, Proposal
import itertools
from math import ceil

from valhalla.common.configdb import ConfigDB
from valhalla.common.rise_set_utils import get_rise_set_intervals, get_largest_interval


PER_MOLECULE_GAP = 5.0             # in-between molecule gap - shared for all instruments
PER_MOLECULE_STARTUP_TIME = 11.0   # per-molecule startup time, which encompasses filter changes


def get_num_mol_changes(molecules):
    return len(list(itertools.groupby([mol['type'].upper() for mol in molecules])))


def get_num_filter_changes(molecules):
    return len(list(itertools.groupby([mol.get('filter', '') for mol in molecules])))


def get_molecule_duration_per_exposure(molecule_dict):
    configdb = ConfigDB()
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


def get_num_exposures(molecule_dict, time_available):
    mol_duration_per_exp = get_molecule_duration_per_exposure(molecule_dict)
    exposure_time = time_available.total_seconds() - PER_MOLECULE_GAP - PER_MOLECULE_STARTUP_TIME
    num_exposures = exposure_time // mol_duration_per_exp

    return max(1, num_exposures)


def get_request_duration(request_dict):
    # calculate the total time needed by the request, based on its instrument and exposures
    configdb = ConfigDB()
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
    return Proposal.objects.get(pk=proposal_id).timeallocation_set.get(
        semester__start__lte=min_window_time,
        semester__end__gte=max_window_time,
        telescope_class=telescope_class)


def get_time_allocation_key(telescope_class, proposal_id, min_window_time, max_window_time):
    time_allocation = get_time_allocation(telescope_class, proposal_id, min_window_time, max_window_time)
    return TimeAllocationKey(time_allocation.semester.id, telescope_class)


def get_total_duration_dict(operator, proposal_id, requests):
    durations = []
    for request in requests:
        min_window_time = min([window['start'] for window in request['windows']])
        max_window_time = max([window['end'] for window in request['windows']])
        tak = get_time_allocation_key(request['location']['telescope_class'],
                                      proposal_id,
                                      min_window_time,
                                      max_window_time
                                      )
        duration = get_request_duration(request)
        durations.append((tak, duration))
    # check the proposal has a time allocation with enough time for all requests depending on operator
    total_duration = {}
    if operator == 'SINGLE':
        (tak, duration) = durations[0]
        total_duration[tak] = duration

    elif operator in ['MANY', 'ONEOF']:
        for (tak, duration) in durations:
            total_duration[tak] = max(total_duration.get(tak, 0.0), duration)
    elif operator == 'AND':
        for (tak, duration) in durations:
            if tak not in total_duration:
                total_duration[tak] = 0
            total_duration[tak] += duration

    return total_duration
