from django.utils import timezone
from datetime import timedelta
import math

from valhalla.userrequests.models import Request
from valhalla.common.rise_set_utils import get_rise_set_intervals_for_site
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

    def _requests(self, instrument_name, site):
        requests = Request.objects.filter(
            windows__start__lte=self.now + timedelta(days=1),
            windows__end__gte=self.now,
            state='PENDING',
            target__type='SIDEREAL'
        )
        if instrument_name:
            requests = requests.filter(molecules__instrument_name=instrument_name).distinct()

        return requests.prefetch_related(
            'molecules', 'windows', 'target', 'constraints', 'location', 'user_request', 'user_request__proposal'
        )

    def _sites(self):
        if self.site:
            return [{'code': self.site}]
        else:
            return configdb.get_site_data()

    def _n_telescopes_available_at_site(self, site, request):
        total_tel = 0
        for molecule in request.molecules.all():
            telescopes_for_instrument_type = configdb.get_telescopes_per_instrument_type(molecule.instrument_name)
            total_tel += min([len(t) for t in telescopes_for_instrument_type if t.site is site], default=0)
        avg_telescopes = total_tel / request.molecules.count()
        return avg_telescopes

    def _visible_intervals(self, request):
        visible_intervals = []
        for site in self.sites:
            if not request.location.site or request.location.site is site:
                intervals = get_rise_set_intervals_for_site(request.as_dict, site['code'])
                for r, s in intervals:
                    if (s-r).seconds >= request.duration and r >= self.now:
                        visible_intervals.append(dict(site=site['code'], interval=(r, s)))
        return visible_intervals

    def _total_time_visible(self, request_intervals):
        # TODO: Compensate for overlap at different sites.
        return sum([(i['interval'][1] - i['interval'][0]).seconds for i in request_intervals])

    def _binned_pressure_by_hours_from_now(self):
        quarter_hour_bins = [{} for x in range(0, 24 * 4)]
        bin_start_times = [self.now + timedelta(minutes=15 * x) for x in range(0, 24 * 4)]

        for request in self.requests:
            visible_intervals = self._visible_intervals(request)
            total_time_visible = self._total_time_visible(visible_intervals)
            if total_time_visible < 1:
                continue
            base_pressure = request.duration / total_time_visible

            for i, bin_start in enumerate(bin_start_times):
                n_telescopes = 0
                for interval in visible_intervals:
                    if interval['interval'][0] <= bin_start < interval['interval'][1]:
                        n_telescopes += self._n_telescopes_available_at_site(interval['site'], request)
                if n_telescopes < 1:
                    continue
                pressure = base_pressure / n_telescopes
                proposal = request.user_request.proposal.id
                # TODO: If self.site is set, only add on pressure from requests that are visible from there.
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
