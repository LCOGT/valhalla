from valhalla.proposals.models import TimeAllocationKey, Proposal
import itertools
from math import ceil

from valhalla.common.configdb import ConfigDB


PER_MOLECULE_GAP = 5.0             # in-between molecule gap - shared for all instruments
PER_MOLECULE_STARTUP_TIME = 11.0   # per-molecule startup time, which encompasses filter changes


def get_num_mol_changes(molecules):
    return len(list(itertools.groupby([mol['type'].upper() for mol in molecules])))


def get_num_filter_changes(molecules):
    return len(list(itertools.groupby([mol.get('filter', '') for mol in molecules])))


def get_molecule_duration(molecule_dict):
    configdb = ConfigDB()
    total_overhead_per_exp = configdb.get_exposure_overhead(molecule_dict['instrument_name'], molecule_dict['bin_x'])
    mol_duration = molecule_dict['exposure_count'] * (molecule_dict['exposure_time'] + total_overhead_per_exp)
    duration = mol_duration + PER_MOLECULE_GAP + PER_MOLECULE_STARTUP_TIME

    return duration


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


def get_total_duration_dict(operator, durations):
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
