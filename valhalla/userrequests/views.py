from django_filters.views import FilterView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateView
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

from valhalla.userrequests.models import UserRequest, Request
from valhalla.userrequests.filters import UserRequestFilter
from valhalla.userrequests.cadence import get_cadence_requests
from valhalla.userrequests.serializers import CadenceRequestSerializer, UserRequestSerializer, RequestSerializer

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


class InstrumentInformationView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, instrument_type):
        configdb = ConfigDB()
        filters = configdb.get_filters(instrument_type)
        filter_map = configdb.get_filter_map()
        return Response({
            'filters': {filter: filter_map[filter] for filter in filters},
            'binnings': configdb.get_binnings(instrument_type),
            'default_binning': configdb.get_default_binning(instrument_type),
        })


class RequestListView(LoginRequiredMixin, FilterView):
    template_name = 'userrequests/request_list.html'
    model = Request
    paginate_by = 20

    def get_queryset(self):
        user_request = get_object_or_404(
            UserRequest,
            pk=self.kwargs['ur'],
            proposal__in=self.request.user.proposal_set.all()
        )
        return user_request.requests.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['userrequest'] = UserRequest.objects.get(pk=self.kwargs['ur'])
        return context


class RequestCreateView(LoginRequiredMixin, TemplateView):
    template_name = 'userrequests/request_create.html'


class CadenceRequestView(APIView):
    ''' Takes a request within a window and with cadence parameters and returns a set of requests
        using the cadence spacing specified.
    '''
    def post(self, request):
        expanded_requests = []
        for req in request.data.get('requests', []):
            if req.get('cadence'):
                cadence_request_serializer = CadenceRequestSerializer(data=req)
                if cadence_request_serializer.is_valid():
                    expanded_requests.extend(get_cadence_requests(cadence_request_serializer.validated_data))
                else:
                    return Response(cadence_request_serializer.errors, status=400)
            else:
                expanded_requests.append(req)

        # now replace the originally sent requests with the cadence requests and send it back
        request.data['requests'] = expanded_requests

        if(len(request.data['requests']) > 1):
            request.data['operator'] = 'MANY'
        ur_serializer = UserRequestSerializer(data=request.data, context={'request': request})
        if not ur_serializer.is_valid():
            return Response(ur_serializer.errors, status=400)
        return Response(request.data)
