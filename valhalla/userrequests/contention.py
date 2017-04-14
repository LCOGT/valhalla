from django.utils import timezone
from datetime import timedelta
import math

from valhalla.userrequests.models import Request
from valhalla.common.rise_set_utils import get_rise_set_intervals, get_site_rise_set_intervals
from valhalla.common.configdb import configdb


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
        ).prefetch_related(
            'molecules', 'windows', 'target', 'constraints', 'location', 'user_request', 'user_request__proposal'
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


class Pressure(object):
    def __init__(self, instrument_name=None, site=None, anonymous=True):
        self.anonymous = anonymous
        self.site = site
        self.requests = self._requests(instrument_name, site)
        self.request_visibility = self._request_visibility()
        self.site_nights = self._site_nights()

    def _requests(self, instrument_name, site):
        requests = Request.objects.filter(
            windows__start__lte=timezone.now() + timedelta(days=1),
            windows__end__gte=timezone.now(),
            state='PENDING',
            target__type='SIDEREAL'
        )
        if instrument_name:
            requests = requests.filter(molecules__instrument_name=instrument_name)

        return requests.prefetch_related(
            'molecules', 'windows', 'target', 'constraints', 'location', 'user_request', 'user_request__proposal'
        )

    def _request_visibility(self):
        vis = {}
        for req in self.requests:
            if req.id not in vis:
                vis[req.id] = sum((s - r).seconds for s, r in get_rise_set_intervals(req.as_dict) if r > timezone.now())
        return vis

    def _site_nights(self):
        site_nights = {}
        if self.site:
            sites = [{'code': self.site}]
        else:
            sites = configdb.get_site_data()
        for site in sites:
            site_nights[site['code']] = get_site_rise_set_intervals(
                timezone.now(), timezone.now() + timedelta(hours=24), site['code']
            )

        return site_nights

    def _available_sites(self, start, end):
        sites = set()
        for site in self.site_nights:
            for rise_set in self.site_nights[site]:
                if rise_set[0] <= start and rise_set[1] >= end:
                    sites.add(site)
        return sites

    def _binned_pressure_by_hours_from_now(self):
        #  Quarter hour bins
        quarter_hour_bins = [{} for x in range(0, 24 * 4)]
        for x in range(0, 24 * 4):
            start = timezone.now() + timedelta(minutes=15 * x)
            end = timezone.now() + timedelta(minutes=15 * (x + 1))
            available_sites = self._available_sites(start, end)
            requests = [
                r for r in self.requests if
                min(w.start for w in r.windows.all()) <= start and max(w.end for w in r.windows.all()) >= end
            ]
            for request in requests:
                proposal = request.user_request.proposal.id
                pressure = self._pressure_for_request(request, available_sites)
                if not quarter_hour_bins[x].get(proposal):
                    quarter_hour_bins[x][proposal] = pressure
                else:
                    quarter_hour_bins[x][proposal] += pressure

        return quarter_hour_bins

    def _pressure_for_request(self, request, available_sites):
        visible_seconds = self.request_visibility[request.id]
        if visible_seconds < 1:
            return 0
        duration = request.duration
        total_tel = 0
        for molecule in request.molecules.all():
            telescopes_for_instrument_type = configdb.get_telescopes_per_instrument_type(molecule.instrument_name)
            total_tel += min([len(t) for t in telescopes_for_instrument_type if t.site in available_sites], default=0)
        if total_tel < 1:
            return 0
        avg_telescopes = total_tel / request.molecules.count()
        return (duration / visible_seconds) / avg_telescopes

    def _anonymize(self, data):
        for index, time in enumerate(data):
            data[index] = {'All Proposals': sum(time.values())}
        return data

    def data(self):
        if self.anonymous:
            return self._anonymize(self._binned_pressure_by_hours_from_now())
        else:
            return self._binned_pressure_by_hours_from_now()
