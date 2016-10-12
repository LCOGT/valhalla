from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.utils.translation import ugettext as _

from valhalla.proposals.models import Semester

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
            modify_ipp_time(new_request.user_request, 'credit', [new_request])
        else:
            if old_request.state == 'WINDOW_EXPIRED':
                try:
                    modify_ipp_time(new_request.user_request, 'debit', [new_request])
                except TimeAllocationError as tae:
                    logger.warn(_('Request {} switched from WINDOW_EXPIRED to COMPLETED but did not have enough '
                                  'ipp_time to debit: {}').format(new_request, repr(tae)))

    if new_request.state == 'CANCELED' or new_request.state == 'WINDOW_EXPIRED':
        ipp_value = new_request.user_request.ipp_value
        if ipp_value >= 1.0:
            modify_ipp_time(new_request.user_request, 'credit', [new_request])


@transaction.atomic
def on_userrequest_state_change(old_userrequest, new_userrequest):
    if old_userrequest.state == new_userrequest.state:
        return
    valid_state_change(old_userrequest.state, new_userrequest.state, old_userrequest)
    if new_userrequest.state == 'COMPLETED':
        if new_userrequest.ipp_value >= 1.0 and new_userrequest.operator == 'oneof':
            requests_to_credit = new_userrequest.requests_set.filter(state__in=['PENDING', 'SCHEDULED'])
            modify_ipp_time(new_userrequest, 'credit', requests_to_credit)
    elif new_userrequest.state in TERMINAL_STATES:
        for r in new_userrequest.request_set.filter(state__in=['PENDING', 'SCHEDULED']):
            r.state = new_userrequest.state
            r.save()


def modify_ipp_time(ur, modification='debit', specific_requests=None):
    if modification != 'debit' and modification != 'credit':
        raise TimeAllocationError(_("modification '{}' is not one of 'debit' or 'credit'").format(modification))

    time_allocations = ur.timeallocations

    time_allocations_dict = {(ta.semester.id, ta.telescope_class): ta for ta in time_allocations.all()}
    # Ipp time debits and credits all requests within the UR at once for submitting and cancelling
    # unless specific requests are submitted
    if not specific_requests:
        specific_requests = ur.request_set.all()

    ipp_value = ur.ipp_value - 1
    if ipp_value == 0.0:
        # Do nothing for an adjusted ipp_value of zero
        return

    # need this dict because of multiple requests within the user request
    modified_ipp_values_dict = {tak: (timedelta(hours=ta.ipp_time_available)).total_seconds()
                                for tak, ta in time_allocations_dict.items()}

    for request in specific_requests:
        tak = request.time_allocation_key

        # Exception: time_remaining > ipp_time_available - request duration * ipp_value
        # This ensures that you cannot go above your max allowable ipp_value
        if request.duration > 0:
            if modification == 'debit':
                if modified_ipp_values_dict[tak] < request.duration*ipp_value:
                    max_ipp_allowable = (modified_ipp_values_dict[tak] / request.duration) + 1.0
                    msg = _(("{} '{}' ipp_value of {} requires more ipp_time then is available. "
                            "Please lower your ipp_value to <= {:.3f} and submit again.")).format(
                            request.location.telescope_class,
                            ur.observation_type,
                            (ipp_value + 1),
                            max_ipp_allowable
                        )
                    raise TimeAllocationError(msg)
                else:
                    # store the debits to the ipp_time here to apply at the end (because if a subsequent
                    # part of the user request throws an exception we don't want to debit anything yet)
                    modified_ipp_values_dict[tak] -= request.duration*ipp_value
            elif modification == 'credit':
                # store the credits to ipp_time here to apply at the end in case an exception is thrown
                modified_ipp_values_dict[tak] += request.duration*abs(ipp_value)

    # No exceptions were raised, so it is safe to debit (or credit) the ipp time at this point
    for tak, ipp_time in modified_ipp_values_dict.items():
        time_allocation = time_allocations_dict[tak]
        # limit the amount that could be credited by the ipp_limit
        time_allocation.ipp_time_available = min(ipp_time / 3600.0, time_allocation.ipp_limit)
        time_allocation.save()


class TimeAllocationError(Exception):
    '''Raised when proposal time used goes above its allocation'''
    pass
