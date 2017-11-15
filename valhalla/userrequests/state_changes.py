from django.utils import timezone
from django.db import transaction
from django.utils.translation import ugettext as _

from valhalla.proposals.models import TimeAllocation, TimeAllocationKey
from valhalla.userrequests.request_utils import exposure_completion_percentage_from_pond_block
from valhalla.userrequests.models import UserRequest, Request

import itertools
import logging
import dateutil.parser
from math import isclose

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
                    logger.warning(_('Request {} switched from WINDOW_EXPIRED to COMPLETED but did not have enough '
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
        for r in new_userrequest.requests.filter(state__in=['PENDING', 'SCHEDULED']):
            r.state = new_userrequest.state
            r.save()


def validate_ipp(ur_dict, total_duration_dict):
    ipp_value = ur_dict['ipp_value'] - 1
    if ipp_value <= 0:
        return

    time_allocations_dict = {tak: TimeAllocation.objects.get(semester__id=tak.semester,
                                                             telescope_class=tak.telescope_class,
                                                             instrument_name=tak.instrument_name,
                                                             proposal__id=ur_dict['proposal']).ipp_time_available
                             for tak in total_duration_dict.keys()}

    for tak, duration in total_duration_dict.items():
        duration_hours = duration / 3600.0
        if time_allocations_dict[tak] < (duration_hours * ipp_value):
            max_ipp_allowable = (time_allocations_dict[tak] / duration_hours) + 1.0
            msg = _(("{}-{}'{}' ipp_value of {} requires more ipp_time then is available. "
                     "Please lower your ipp_value to <= {:.3f} and submit again.")).format(
                tak.telescope_class,
                tak.instrument_name,
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
        time_allocations_dict = {TimeAllocationKey(ta.semester.id, ta.telescope_class, ta.instrument_name): ta
                                 for ta in time_allocations.all()}

        total_duration_dict = ur.total_duration
        for tak, duration in total_duration_dict.items():
            duration_hours = duration / 3600.0
            time_allocations_dict[tak].ipp_time_available -= (ipp_value * duration_hours)
            time_allocations_dict[tak].save()
    except Exception as e:
        logger.warning(_("Problem debitting ipp on creation for ur {} on proposal {}: {}")
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
                logger.warning(_("ipp debiting for request {} would set ipp_time_available < 0. "
                                 "Time available after debiting will be capped at 0").format(request.id))
                modified_time = 0
            elif modified_time > time_allocation.ipp_limit:
                logger.warning(_("ipp crediting for request {} would set ipp_time_available > ipp_limit. "
                                 "Time available after crediting will be capped at ipp_limit"))
                modified_time = time_allocation.ipp_limit
            time_allocation.ipp_time_available = modified_time
            time_allocation.save()
    except Exception as e:
        logger.warning(_("Problem {}ing ipp time for request {}: {}").format(modification, request.id, repr(e)))


def get_request_state_from_pond_blocks(request_state, acceptability_threshold, request_blocks):
    active_blocks = False
    future_blocks = False
    now = timezone.now()
    for block in request_blocks:
        start_time = dateutil.parser.parse(block['start']).replace(tzinfo=timezone.utc)
        end_time = dateutil.parser.parse(block['end']).replace(tzinfo=timezone.utc)
        # mark a block as complete if a % of the total exposures of all its molecules are complete
        completion_percent = exposure_completion_percentage_from_pond_block(block)
        if isclose(acceptability_threshold, completion_percent) or completion_percent >= acceptability_threshold:
            return 'COMPLETED'
        if (not block['canceled'] and not any(molecule['failed'] for molecule in block['molecules'])
                and start_time < now < end_time):
            active_blocks = True
        if now < start_time:
            future_blocks = True

    if not (future_blocks or active_blocks):
        return 'FAILED'

    return request_state


def update_request_state(request, request_blocks, ur_expired):
    '''Update a request state given a set of pond blocks for that request'''
    if request.state == 'COMPLETED':
        return False

    state_changed = False
    fail_count = 0

    # Get the state from the pond blocks
    new_r_state = get_request_state_from_pond_blocks(request.state, request.acceptability_threshold, request_blocks)
    # update the fail_count if the pond state was failed, before overwriting pond state
    if new_r_state == 'FAILED':
        fail_count = 1
    # If the state is not a terminal state and the ur has expired, mark the request as expired
    if new_r_state not in TERMINAL_STATES and ur_expired:
        new_r_state = 'WINDOW_EXPIRED'
    # If the state was the 'FAILED' fake state, switch it to pending but record that the state has changed
    elif new_r_state == 'FAILED' and request.state not in TERMINAL_STATES:
        new_r_state = 'PENDING'
        state_changed = True
    with transaction.atomic():
        # Re-get the request and lock. If the new state is a valid state transition, set it on the request atomically.
        req = Request.objects.select_for_update().get(pk=request.id)
        req.fail_count += fail_count
        if new_r_state in REQUEST_STATE_MAP[req.state]:
            state_changed = True
            req.state = new_r_state
        req.save()

    return state_changed


def aggregate_request_states(user_request):
    '''Aggregate the state of the user request from all of its child request states'''
    request_states = [request.state for request in Request.objects.filter(user_request=user_request)]
    # Set the priority ordering - assume AND by default
    state_priority = ['WINDOW_EXPIRED', 'PENDING', 'COMPLETED', 'CANCELED']
    if user_request.operator == 'ONEOF':
        state_priority = ['COMPLETED', 'PENDING', 'WINDOW_EXPIRED', 'CANCELED']
    elif user_request.operator == 'MANY':
        state_priority = ['PENDING', 'COMPLETED', 'WINDOW_EXPIRED', 'CANCELED']

    for state in state_priority:
        if state in request_states:
            return state

    raise AggregateStateException('Unable to Aggregate States: {}'.format(request_states))


def update_request_states_for_window_expiration():
    '''Update the state of all requests and user_requests to WINDOW_EXPIRED if their last window has passed'''
    now = timezone.now()
    states_changed = False
    for user_request in UserRequest.objects.exclude(state__in=TERMINAL_STATES):
        request_states_changed = False
        for request in user_request.requests.filter(state='PENDING').prefetch_related('windows'):
            if request.max_window_time < now:
                logger.info('Expiring request %s', request.id, extra={'tags': {'request_num': request.id}})
                with transaction.atomic():
                    req = Request.objects.select_for_update().get(pk=request.id)
                    if req.state == 'PENDING':
                        req.state = 'WINDOW_EXPIRED'
                        states_changed = True
                        request_states_changed = True
                        req.save()
        if request_states_changed:
            update_user_request_state(user_request)

    return states_changed


def update_request_states_from_pond_blocks(pond_blocks):
    '''Update the states of requests and user_requests given a set of recently changed pond blocks.'''
    blocks_with_tracking_nums = [pb for pb in pond_blocks if pb['molecules'][0]['tracking_num']]
    sorted_blocks_with_tracking_nums = sorted(blocks_with_tracking_nums, key=lambda x: x['molecules'][0]['tracking_num'])
    blocks_by_tracking_num = itertools.groupby(sorted_blocks_with_tracking_nums, lambda x: x['molecules'][0]['tracking_num'])
    now = timezone.now()
    states_changed = False

    for tracking_num, blocks in blocks_by_tracking_num:
        sorted_blocks_by_request = sorted(blocks, key=lambda x: x['molecules'][0]['request_num'])
        blocks_by_request_num = {int(k): list(v) for k, v in itertools.groupby(sorted_blocks_by_request, key=lambda x: x['molecules'][0]['request_num'])}
        user_request = UserRequest.objects.prefetch_related('requests').get(pk=tracking_num)
        ur_expired = user_request.max_window_time < now
        requests = user_request.requests.all()
        for request in requests:
            if request.id in blocks_by_request_num:
                states_changed |= update_request_state(request, blocks_by_request_num[request.id], ur_expired)
        states_changed |= update_user_request_state(user_request)

    return states_changed


def update_user_request_state(user_request):
    '''Update the state of the user request if possible'''
    new_ur_state = aggregate_request_states(user_request)
    with transaction.atomic():
        ur = UserRequest.objects.select_for_update().get(pk=user_request.id)
        if new_ur_state in REQUEST_STATE_MAP[ur.state]:
            ur.state = new_ur_state
            ur.save()
            return True
    return False


class AggregateStateException(Exception):
    '''Raised when we fail to aggregate request states into a user request state'''
    pass


class TimeAllocationError(Exception):
    '''Raised when proposal time used goes above its allocation'''
    pass
