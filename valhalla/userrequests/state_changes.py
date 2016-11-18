from django.utils import timezone
from django.db import transaction
from django.utils.translation import ugettext as _
from valhalla.proposals.models import TimeAllocation, TimeAllocationKey

import logging

logger = logging.getLogger(__name__)


REQUEST_STATE_MAP = {
    'PENDING': ['SCHEDULED', 'FAILED', 'COMPLETED', 'WINDOW_EXPIRED', 'CANCELED'],
    'COMPLETED': [],
    'SCHEDULED': ['PENDING', 'COMPLETED', 'WINDOW_EXPIRED', 'CANCELED'],
    'WINDOW_EXPIRED': ['COMPLETED'],
    'CANCELED': ['COMPLETED'],
}

TERMINAL_STATES = ['COMPLETED', 'CANCELED', 'WINDOW_EXPIRED']


class InvalidStateChange(Exception):
    pass


def valid_state_change(old_state, new_state, obj):
    if new_state not in REQUEST_STATE_MAP[old_state]:
        raise InvalidStateChange(_("Cannot transition from request state {} to {} for {}").format(
            old_state, new_state, obj
        ))


@transaction.atomic
def on_request_state_change(old_request, new_request):
    if old_request.state == new_request.state:
        return
    valid_state_change(old_request.state, new_request.state, old_request)
    # it must be a valid transition, so do time accounting here
    if new_request.state == 'COMPLETED':
        new_request.completed = timezone.now()
        ipp_value = new_request.user_request.ipp_value
        if ipp_value < 1.0:
            modify_ipp_time_from_requests(ipp_value, [new_request], 'credit')
        else:
            if old_request.state == 'WINDOW_EXPIRED':
                try:
                    modify_ipp_time_from_requests(ipp_value, [new_request], 'debit')
                except TimeAllocationError as tae:
                    logger.warn(_('Request {} switched from WINDOW_EXPIRED to COMPLETED but did not have enough '
                                  'ipp_time to debit: {}').format(new_request, repr(tae)))

    if new_request.state == 'CANCELED' or new_request.state == 'WINDOW_EXPIRED':
        ipp_value = new_request.user_request.ipp_value
        if ipp_value >= 1.0:
            modify_ipp_time_from_requests(ipp_value, [new_request], 'credit')


@transaction.atomic
def on_userrequest_state_change(old_userrequest, new_userrequest):
    if old_userrequest.state == new_userrequest.state:
        return
    valid_state_change(old_userrequest.state, new_userrequest.state, old_userrequest)
    if new_userrequest.state == 'COMPLETED':
        if new_userrequest.ipp_value >= 1.0 and new_userrequest.operator == 'oneof':
            requests_to_credit = new_userrequest.requests_set.filter(state__in=['PENDING', 'SCHEDULED'])
            modify_ipp_time_from_requests(new_userrequest.ipp_value, requests_to_credit, 'credit')
    elif new_userrequest.state in TERMINAL_STATES:
        for r in new_userrequest.request_set.filter(state__in=['PENDING', 'SCHEDULED']):
            r.state = new_userrequest.state
            r.save()


def validate_ipp(ur_dict, total_duration_dict):
    ipp_value = ur_dict['ipp_value'] - 1
    if ipp_value <= 0:
        return

    time_allocations_dict = {tak: TimeAllocation.objects.get(semester__id=tak.semester,
                                                             telescope_class=tak.telescope_class,
                                                             proposal__id=ur_dict['proposal']).ipp_time_available
                             for tak in total_duration_dict.keys()}

    for tak, duration in total_duration_dict.items():
        duration_hours = duration / 3600.0
        if time_allocations_dict[tak] < (duration_hours * ipp_value):
            max_ipp_allowable = (time_allocations_dict[tak] / duration_hours) + 1.0
            msg = _(("{} '{}' ipp_value of {} requires more ipp_time then is available. "
                     "Please lower your ipp_value to <= {:.3f} and submit again.")).format(
                tak.telescope_class,
                ur_dict['observation_type'],
                (ipp_value + 1),
                max_ipp_allowable
            )
            raise TimeAllocationError(msg)
        time_allocations_dict[tak] -= (duration_hours * ipp_value)


def debit_ipp_time(ur):
    ipp_value = ur.ipp_value - 1
    if ipp_value <= 0:
        return
    try:
        time_allocations = ur.timeallocations
        time_allocations_dict = {TimeAllocationKey(ta.semester.id, ta.telescope_class): ta
                                 for ta in time_allocations.all()}

        total_duration_dict = ur.total_duration
        for tak, duration in total_duration_dict.items():
            duration_hours = duration / 3600.0
            time_allocations_dict[tak].ipp_time_available -= (ipp_value * duration_hours)
            time_allocations_dict[tak].save()
    except Exception as e:
        logger.warn(_("Problem debitting ipp on creation for ur {} on proposal {}: {}")
                    .format(ur.id, ur.proposal.id, repr(e)))


def modify_ipp_time_from_requests(ipp_val, requests_list, modification='debit'):
    ipp_value = ipp_val - 1
    if ipp_value == 0:
        return
    try:
        for request in requests_list:
            time_allocation = request.timeallocation
            duration_hours = request.duration / 3600.0
            modified_time = time_allocation.ipp_time_available
            if modification == 'debit':
                modified_time -= (duration_hours * ipp_value)
            elif modification == 'credit':
                modified_time += abs(ipp_value) * duration_hours
            if modified_time < 0:
                logger.warn(_("ipp debiting for request {} would set ipp_time_available < 0. "
                            "Time available after debiting will be capped at 0").format(request.id))
                modified_time = 0
            elif modified_time > time_allocation.ipp_limit:
                logger.warn(_("ipp crediting for request {} would set ipp_time_available > ipp_limit. "
                              "Time available after crediting will be capped at ipp_limit"))
                modified_time = time_allocation.ipp_limit
            time_allocation.ipp_time_available = modified_time
            time_allocation.save()
    except Exception as e:
        logger.warn(_("Problem {}ing ipp time for request {}: {}").format(modification, request.id, repr(e)))


class TimeAllocationError(Exception):
    '''Raised when proposal time used goes above its allocation'''
    pass