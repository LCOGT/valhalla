from __future__ import absolute_import, unicode_literals
from valhalla.proposals.models import Semester, TimeAllocation
from valhalla.proposals.accounting import query_pond
from valhalla.userrequests.models import UserRequest

from django.conf import settings
from celery import shared_task
import requests
import logging

logger = logging.getLogger(__name__)

def query_pond_for_time_used(request):
    logger.info('Attempting to get time used for %s', request.id)
    url = '{0}/pond/pond/accounting/{}/'.format(settings.POND_URL, request.id)
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

@shared_task
# Make this a transaction to avoid race conditions
def update_time_allocation(request):

    std_total = (talloc, talloc.semester.start, talloc.semester.end, too=False)
    too_total = get_time_totals_from_pond(talloc, talloc.semester.start, talloc.semester.end, too=True)
    talloc.std_time_used = std_total
    talloc.too_time_used = too_total
    talloc.save()


@shared_task
def run_accounting(userrequest):
    for request in userrequest.requests:
        logger.info('Performing accounting for request: %s', request)
        talloc = request.timeallocation
        logger.info('Updating timeallocation for %s', talloc.proposal, extra={'tags': {'proposal': talloc.proposal.id}})
        time_used = query_pond_for_time_used(request)
        if request.user_request.observation_type = UserRequest.TOO:
            talloc.too_time_used += time_used['block_bounded_attempted_hours']
        else:
            talloc.std_time_used += time_used['attempted_hours']
        talloc.save()
