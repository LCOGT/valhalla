from django_filters.views import FilterView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.http import HttpResponseBadRequest
from django.utils import timezone
from dateutil.parser import parse
from datetime import timedelta
from rest_framework.views import APIView

from valhalla.common.configdb import ConfigDB
from valhalla.common.telescope_states import (get_telescope_states, get_telescope_availability_per_day,
                                              combine_telescope_availabilities_by_site_and_class)
from valhalla.userrequests.request_utils import get_airmasses_for_request_at_sites
from valhalla.userrequests.models import UserRequest, Request
from valhalla.userrequests.serializers import RequestSerializer
from valhalla.userrequests.filters import UserRequestFilter


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


class UserRequestListView(FilterView):
    filterset_class = UserRequestFilter
    template_name = 'userrequests/userrequest_list.html'
    paginate_by = 20

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return UserRequest.objects.filter(proposal__in=self.request.user.proposal_set.all())
        else:
            return UserRequest.objects.none()


class UserRequestDetailView(DetailView):
    model = UserRequest

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return UserRequest.objects.filter(proposal__in=self.request.user.proposal_set.all())
        else:
            return UserRequest.objects.none()


class RequestDetailView(DetailView):
    model = Request

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Request.objects.filter(user_request__proposal__in=self.request.user.proposal_set.all())
        else:
            return Request.objects.none()


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
        configdb = ConfigDB()
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


