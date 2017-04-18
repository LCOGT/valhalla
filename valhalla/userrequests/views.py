from django_filters.views import FilterView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django.http import HttpResponseBadRequest, HttpResponseServerError
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from dateutil.parser import parse
from datetime import timedelta
import requests
from rest_framework.views import APIView

from valhalla.common.configdb import configdb
from valhalla.common.telescope_states import (get_telescope_states, get_telescope_availability_per_day,
                                              combine_telescope_availabilities_by_site_and_class)
from valhalla.userrequests.request_utils import get_airmasses_for_request_at_sites
from valhalla.userrequests.models import UserRequest, Request
from valhalla.userrequests.serializers import RequestSerializer
from valhalla.userrequests.filters import UserRequestFilter
from valhalla.userrequests.state_changes import update_request_states_from_pond_blocks
from valhalla.userrequests.contention import Contention, Pressure


def get_start_end_paramters(request):
    try:
        start = parse(request.query_params.get('start'))
    except TypeError:
        start = timezone.now() - timedelta(days=1)
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
    paginate_by = 20

    def get_queryset(self):
        return userrequest_queryset(self.request)


class UserRequestDetailView(DetailView):
    model = UserRequest

    def get_queryset(self):
        return userrequest_queryset(self.request)


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
            start, end = get_start_end_paramters(request)
        except ValueError as e:
            return HttpResponseBadRequest(str(e))
        sites = request.query_params.getlist('site')
        telescopes = request.query_params.getlist('telescope')
        telescope_states = get_telescope_states(start, end, sites=sites, telescopes=telescopes)
        str_telescope_states = {str(k): v for k, v in telescope_states.items()}

        return Response(str_telescope_states)


class TelescopeAvailabilityView(APIView):
    ''' Retrieves the nightly % availability of each telescope between the start and end times
    '''
    permission_classes = (AllowAny,)

    def get(self, request):
        try:
            start, end = get_start_end_paramters(request)
        except ValueError as e:
            return HttpResponseBadRequest(str(e))
        combine = request.query_params.get('combine')
        sites = request.query_params.getlist('sites')
        telescopes = request.query_params.getlist('telescope')
        telescope_availability = get_telescope_availability_per_day(
            start, end, sites=sites, telescopes=telescopes
        )
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

        last_query_time = cache.get('isDirty_query_time', (timezone.now() - timedelta(days=7)))
        url = settings.POND_URL + '/pond/pond/blocks/new/?since={}'.format(last_query_time)
        now = timezone.now()
        try:
            response = requests.get(url)
            response.raise_for_status()
        except Exception as e:
            return HttpResponseServerError({'error': repr(e)})

        pond_blocks = response.json()
        is_dirty = update_request_states_from_pond_blocks(pond_blocks)
        cache.set('isDirty_query_time', now)

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
