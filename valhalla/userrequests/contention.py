from django.utils import timezone
from datetime import timedelta
import math

from valhalla.userrequests.models import Request


class Contention(object):
    def __init__(self, instrument_name, anonymous=True):
        self.anonymous = anonymous
        self.requests = self._requests(instrument_name)

    def _requests(self, instrument_name):
        return Request.objects.filter(
            windows__start__lt=timezone.now() + timedelta(days=1),
            windows__end__gt=timezone.now(),
            state='PENDING',
            molecules__instrument_name=instrument_name,
            target__type='SIDEREAL'
        )

    def _binned_durations_by_proposal_and_ra(self):
        ra_bins = [{} for x in range(0, 24)]
        for request in self.requests:
            ra = math.floor(request.target.ra / 15)
            proposal_id = request.user_request.proposal.id
            if not ra_bins[ra].get(proposal_id):
                ra_bins[ra][proposal_id] = request.duration
            else:
                ra_bins[ra][proposal_id] += request.duration
        return ra_bins

    def _anonymize(self, data):
        for index, ra in enumerate(data):
            data[index] = {'All Proposals': sum(ra.values())}
        return data

    def data(self):
        if self.anonymous:
            return self._anonymize(self._binned_durations_by_proposal_and_ra())
        else:
            return self._binned_durations_by_proposal_and_ra()
