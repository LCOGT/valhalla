from django.utils import timezone
from datetime import timedelta
import math

from valhalla.userrequests.models import Request
from valhalla.common.rise_set_utils import get_rise_set_intervals
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
        self.now = timezone.now()
        self.requests = self._requests(instrument_name, site)
        self.site = site
        self.sites = self._sites()
        self.telescopes = {}

    def _requests(self, instrument_name, site):
        requests = Request.objects.filter(
            windows__start__lte=self.now + timedelta(days=1),
            windows__end__gte=self.now,
            state='PENDING',
            target__type='SIDEREAL'
        )
        if instrument_name:
            requests = requests.filter(molecules__instrument_name=instrument_name)

        return requests.prefetch_related(
            'molecules', 'windows', 'target', 'constraints', 'location', 'user_request', 'user_request__proposal'
        ).distinct()

    def _telescopes(self, instrument_name):
        if instrument_name not in self.telescopes:
            telescopes = configdb.get_telescopes_per_instrument_type(instrument_name, only_schedulable=True)
            self.telescopes[instrument_name] = telescopes
        return self.telescopes[instrument_name]

    def _sites(self):
        if self.site:
            return [{'code': self.site}]
        else:
            return configdb.get_site_data()

    def _n_possible_telescopes(self, time, site_intervals, instrument_name):
        n_telescopes = 0
        for site in site_intervals:
            for interval in site_intervals[site]:
                if interval[0] <= time < interval[1]:
                    n_telescopes += sum([1 for t in self._telescopes(instrument_name) if t.site == site])
        return n_telescopes

    def _visible_intervals(self, request):
        visible_intervals = {}
        for site in self.sites:
            if not request.location.site or request.location.site == site['code']:
                intervals = get_rise_set_intervals(request.as_dict, site['code'])
                for r, s in intervals:
                    if (s-r).seconds >= request.duration and s > self.now:
                        if site['code'] in visible_intervals:
                            visible_intervals[site['code']].append((r, s))
                        else:
                            visible_intervals[site['code']] = [(r, s)]
        return visible_intervals

    def _time_visible(self, site_intervals):
        return sum(sum((s - r).seconds for r, s in site_intervals[site]) for site in site_intervals)

    def _binned_pressure_by_hours_from_now(self):
        quarter_hour_bins = [{} for x in range(0, 24 * 4)]
        bin_start_times = [self.now + timedelta(minutes=15 * x) for x in range(0, 24 * 4)]

        for request in self.requests:
            site_intervals = self._visible_intervals(request)
            total_time_visible = self._time_visible(site_intervals)
            instrument_name = request.molecules.all()[0].instrument_name

            if total_time_visible < 1:
                continue

            base_pressure = request.duration / total_time_visible
            for i, bin_start in enumerate(bin_start_times):
                n_telescopes = self._n_possible_telescopes(bin_start, site_intervals, instrument_name)

                if n_telescopes < 1:
                    continue

                pressure = base_pressure / n_telescopes
                proposal = request.user_request.proposal.id
                if not quarter_hour_bins[i].get(proposal):
                    quarter_hour_bins[i][proposal] = pressure
                else:
                    quarter_hour_bins[i][proposal] += pressure
        return quarter_hour_bins

    def _anonymize(self, data):
        for index, time in enumerate(data):
            data[index] = {'All Proposals': sum(time.values())}
        return data

    def data(self):
        if self.anonymous:
            return self._anonymize(self._binned_pressure_by_hours_from_now())
        else:
            return self._binned_pressure_by_hours_from_now()
