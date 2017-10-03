from valhalla.userrequests.models import UserRequest

import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def query_pond(request):
    logger.info('Attempting to get time used for %s', request.id)
    url = '{0}/pond/pond/accounting/{}/'.format(settings.POND_URL, request.id)
    response = requests.get(url)
    response.raise_for_status()
    if request.user_request.observation_type == UserRequest.TOO:
        return response.json()['block_bounded_attempted_hours']
    else:
        return response.json()['attempted_hours']
