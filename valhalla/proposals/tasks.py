from __future__ import absolute_import, unicode_literals
from valhalla.userrequests.models import UserRequest, Request

from django.conf import settings
from celery import shared_task
import requests
import logging

logger = logging.getLogger(__name__)


def query_pond_for_time_used(request):
    logger.info('Attempting to get time used for %s', request.id)
    url = '{0}/pond/pond/accounting/{1}/'.format(settings.POND_URL, request.id)
    response = requests.get(url)
    response.raise_for_status()
    return {
        'too_time': response.json()['block_bounded_attempted_hours'],
        'std_time': response.json()['attempted_hours']
    }


@shared_task()
def run_accounting():
    for request in Request.need_accounting():
        log_tags = {'tags': {'proposal': request.user_request.proposal.id}}
        try:
            talloc = request.timeallocation
            logger.info('Performing accounting for request: %s', request.id, extra=log_tags)
            time_used = query_pond_for_time_used(request)
            if request.user_request.observation_type == UserRequest.TOO:
                talloc.too_time_used += time_used['too_time']
            else:
                talloc.std_time_used += time_used['std_time']
            talloc.save()
            request.accounted = True
            request.save()
        except Exception as exc:
            logger.error('Could not run accounting for request %s: %s', request.id, exc, extra=log_tags)
