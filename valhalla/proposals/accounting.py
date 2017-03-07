import logging
import requests
from django.conf import settings

from valhalla.proposals.models import Semester

logger = logging.getLogger(__name__)


def split_time(start, end, chunks=4):
    spans = []
    chunk = (end - start) / chunks
    spans.append((start, start + chunk))
    for i in range(0, chunks - 1):
        spans.append((spans[i][1], spans[i][1] + chunk))
    return spans


def get_time_totals_from_pond(timeallocation, start, end, too, recur=0):
    """
    Pond queries are too slow with large proposals and time out, this hack splits the query
    when a timeout occurs
    """
    if recur > 3:
        raise RecursionError('Pond is timing out, too much recursion.')

    total = 0
    try:
        total += query_pond(timeallocation.proposal.id, start, end, timeallocation.telescope_class, too)
    except requests.HTTPError:
        logger.warning('We got a pond inception. Splitting further.')
        for start, end in split_time(start, end, 4):
            total += get_time_totals_from_pond(timeallocation, start, end, too, recur=recur + 1)

    return total


def query_pond(proposal_id, start, end, telescope_class, too):
    logger.warn('Attempting to get time used for {0} from {1} to {2}'.format(proposal_id, start, end))
    url = '{0}/pond/pond/accounting/summary?proposal_id={1}&start={2}&end={3}&telescope_class={4}&too_time={5}'.format(
        settings.POND_URL, proposal_id, start.strftime('%Y-%m-%d %H:%M:%S'), end.strftime('%Y-%m-%d %H:%M:%S'), telescope_class, too
    )
    response = requests.get(url)
    response.raise_for_status()
    if too:
        return response.json()['block_bounded_attempted_hours']
    else:
        return response.json()['attempted_hours']


def perform_accounting(semesters=list()):
    if not semesters:
        semesters = Semester.current_semesters()

    for semester in semesters:
        logger.warn('Performing accounting for semester: {}'.format(semester))
        for talloc in semester.timeallocation_set.all():
            logger.warn('Updating timeallocation for {}'.format(talloc.proposal))
            std_total = get_time_totals_from_pond(talloc, semester.start, semester.end, too=False)
            too_total = get_time_totals_from_pond(talloc, semester.start, semester.end, too=True)

            talloc.std_time_used = std_total
            talloc.too_time_used = too_total
            talloc.save()
