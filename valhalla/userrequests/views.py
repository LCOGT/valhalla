from django_filters.views import FilterView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django.http import HttpResponseBadRequest, HttpResponseServerError, HttpResponseRedirect
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from django.core.cache import cache
from dateutil.parser import parse
from datetime import timedelta
from rest_framework.views import APIView
import logging

from valhalla.common.configdb import configdb
from valhalla.common.telescope_states import (TelescopeStates, get_telescope_availability_per_day,
                                              combine_telescope_availabilities_by_site_and_class,
                                              ElasticSearchException)
from valhalla.userrequests.request_utils import get_airmasses_for_request_at_sites, return_paginated_results
from valhalla.userrequests.models import UserRequest, Request
from valhalla.userrequests.serializers import RequestSerializer
from valhalla.userrequests.filters import UserRequestFilter
from valhalla.userrequests.state_changes import update_request_states_from_pond_blocks
from valhalla.userrequests.contention import Contention, Pressure

logger = logging.getLogger(__name__)


def get_start_end_paramters(request, default_days_back):
    try:
        start = parse(request.query_params.get('start'))
    except TypeError:
        start = timezone.now() - timedelta(days=default_days_back)
    start = start.replace(tzinfo=timezone.utc)
    try:
        end = parse(request.query_params.get('end'))
    except TypeError:
        end = timezone.now()
    end = end.replace(tzinfo=timezone.utc)
    return start, end


def userrequest_queryset(request):
    if request.user.is_authenticated:
        if request.user.profile.staff_view and request.user.is_staff:
            userrequests = UserRequest.objects.all()
        else:
            userrequests = UserRequest.objects.filter(proposal__in=request.user.proposal_set.all())
            if request.user.profile.view_authored_requests_only:
                userrequests = userrequests.filter(submitter=request.user)
    else:
        userrequests = UserRequest.objects.filter(proposal__public=True)

    return userrequests


class UserRequestListView(FilterView):
    filterset_class = UserRequestFilter
    template_name = 'userrequests/userrequest_list.html'
    strict = False  # TODO remove when https://github.com/carltongibson/django-filter/issues/930 is fixed

    def get_queryset(self):
        return userrequest_queryset(self.request)

    def get_paginate_by(self, qs):
        return self.request.GET.get('paginate_by', 20)


class UserRequestDetailView(DetailView):
    model = UserRequest

    def get_queryset(self):
        return userrequest_queryset(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        requests = self.get_object().requests.all().order_by('id')
        paginator = Paginator(requests, 25)
        page = self.request.GET.get('page')
        try:
            requests = paginator.page(page)
        except PageNotAnInteger:
            requests = paginator.page(1)
        except EmptyPage:
            requests = paginator.page(paginator.num_pages)
        context['requests'] = requests

        return context

    def render_to_response(self, context, **kwargs):
        if self.get_object().requests.count() == 1:
            request = self.get_object().requests.first()
            return HttpResponseRedirect(reverse('userrequests:request-detail', args=(request.id, )))
        else:
            return super().render_to_response(context, **kwargs)


class RequestDetailView(DetailView):
    model = Request

    def get_queryset(self):
        if self.request.user.is_authenticated:
            if self.request.user.profile.staff_view and self.request.user.is_staff:
                requests = Request.objects.all()
            else:
                requests = Request.objects.filter(user_request__proposal__in=self.request.user.proposal_set.all())
                if self.request.user.profile.view_authored_requests_only:
                    requests = requests.filter(user_request__submitter=self.request.user)
        else:
            requests = Request.objects.filter(user_request__proposal__public=True)

        return requests


class RequestCreateView(LoginRequiredMixin, TemplateView):
    template_name = 'userrequests/request_create.html'


class TelescopeStatesView(APIView):
    ''' Retrieves the telescope states for all telescopes between the start and end times
    '''
    permission_classes = (AllowAny,)

    def get(self, request):
        try:
            start, end = get_start_end_paramters(request, default_days_back=0)
        except ValueError as e:
            return HttpResponseBadRequest(str(e))
        sites = request.query_params.getlist('site')
        telescopes = request.query_params.getlist('telescope')
        telescope_states = TelescopeStates(start, end, sites=sites, telescopes=telescopes).get()
        str_telescope_states = {str(k): v for k, v in telescope_states.items()}

        return Response(str_telescope_states)


class TelescopeAvailabilityView(APIView):
    ''' Retrieves the nightly % availability of each telescope between the start and end times
    '''
    permission_classes = (AllowAny,)

    def get(self, request):
        try:
            start, end = get_start_end_paramters(request, default_days_back=1)
        except ValueError as e:
            return HttpResponseBadRequest(str(e))
        combine = request.query_params.get('combine')
        sites = request.query_params.getlist('site')
        telescopes = request.query_params.getlist('telescope')
        try:
            telescope_availability = get_telescope_availability_per_day(
                start, end, sites=sites, telescopes=telescopes
            )
        except ElasticSearchException:
            logger.warning('Error connecting to ElasticSearch. Is SBA reachable?')
            return Response('ConnectionError')
        if combine:
            telescope_availability = combine_telescope_availabilities_by_site_and_class(telescope_availability)
        str_telescope_availability = {str(k): v for k, v in telescope_availability.items()}

        return Response(str_telescope_availability)


class AirmassView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = RequestSerializer(data=request.data)
        if serializer.is_valid():
            return Response(get_airmasses_for_request_at_sites(serializer.validated_data))
        else:
            return Response(serializer.errors)


class InstrumentsInformationView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        info = {}
        for instrument_type in configdb.get_active_instrument_types({}):
            filters = configdb.get_filters(instrument_type)
            filter_map = configdb.get_filter_map()
            info[instrument_type] = {
                'type': 'SPECTRA' if configdb.is_spectrograph(instrument_type) else 'IMAGE',
                'class': instrument_type[0:3],
                'name': configdb.get_instrument_name(instrument_type),
                'filters': {filter: filter_map[filter] for filter in filters},
                'binnings': configdb.get_binnings(instrument_type),
                'default_binning': configdb.get_default_binning(instrument_type),
            }
        return Response(info)


class UserRequestStatusIsDirty(APIView):
    '''
        Gets the pond blocks changed since last call, and updates request and ur statuses with them. Returns if any
        pond_blocks were received from the pond (isDirty)
    '''
    permission_classes = (IsAdminUser,)

    def get(self, request):
        try:
            last_query_time = parse(request.query_params.get('last_query_time'))
        except (TypeError, ValueError):
            last_query_time = cache.get('isDirty_query_time', (timezone.now() - timedelta(days=7)))

        url = settings.POND_URL + '/blocks/?modified_after={0}&canceled=False&limit=1000'.format(last_query_time.strftime('%Y-%m-%dT%H:%M:%S.%f'))
        now = timezone.now()
        pond_blocks = []
        try:
            pond_blocks = return_paginated_results(pond_blocks, url)
        except Exception as e:
            return HttpResponseServerError({'error': repr(e)})

        is_dirty = update_request_states_from_pond_blocks(pond_blocks)
        cache.set('isDirty_query_time', now, None)

        # also factor in if a change in requests (added, updated, cancelled) has occurred since we last checked
        last_update_time = max(Request.objects.latest('modified').modified,
                               UserRequest.objects.latest('modified').modified)
        is_dirty |= last_update_time >= last_query_time

        return Response({'isDirty': is_dirty})


class ContentionView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, instrument_name):
        if request.user.is_staff:
            contention = Contention(instrument_name, anonymous=False)
        else:
            contention = Contention(instrument_name)
        return Response(contention.data())


class PressureView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        instrument_name = request.GET.get('instrument')
        site = request.GET.get('site')
        if request.user.is_staff:
            pressure = Pressure(instrument_name, site, anonymous=False)
        else:
            pressure = Pressure(instrument_name, site)
        return Response(pressure.data())
