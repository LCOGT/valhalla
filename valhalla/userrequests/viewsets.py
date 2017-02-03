from rest_framework import viewsets, filters
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response

from valhalla.common.rise_set_utils import get_rise_set_intervals, get_largest_interval
from valhalla.userrequests.models import UserRequest, Request, DraftUserRequest
from valhalla.userrequests.filters import UserRequestFilter, RequestFilter
from valhalla.userrequests.metadata import RequestMetadata
from valhalla.userrequests.cadence import expand_cadence_request
from valhalla.userrequests.serializers import RequestSerializer, UserRequestSerializer
from valhalla.userrequests.serializers import DraftUserRequestSerializer, CadenceRequestSerializer
from valhalla.userrequests.duration_utils import (get_request_duration, get_molecule_duration_per_exposure,
                                                  PER_MOLECULE_GAP, PER_MOLECULE_STARTUP_TIME)
from valhalla.userrequests.request_utils import (get_airmasses_for_request_at_sites,
                                                 get_telescope_states_for_request)


class UserRequestViewSet(viewsets.ModelViewSet):
    serializer_class = UserRequestSerializer
    filter_class = UserRequestFilter
    filter_backends = (
        filters.DjangoFilterBackend,
        filters.OrderingFilter
    )
    ordering = ('-id',)

    def get_queryset(self):
        if self.request.user.is_staff:
            return UserRequest.objects.all()
        elif self.request.user.is_authenticated():
            return UserRequest.objects.filter(
                proposal__in=self.request.user.proposal_set.all()
            )
        else:
            return UserRequest.objects.none()

    @list_route(methods=['post'])
    def validate(self, request):
        serializer = UserRequestSerializer(data=request.data, context={'request': request})
        req_durations = {}
        if serializer.is_valid():
            req_durations['requests'] = []
            for req in serializer.validated_data['requests']:
                req_info = {'duration': get_request_duration(req)}
                mol_durations = [{'duration': get_molecule_duration_per_exposure(mol)} for mol in req['molecules']]
                req_info['molecules'] = mol_durations
                req_info['largest_interval'] = get_largest_interval(get_rise_set_intervals(req)).total_seconds()
                req_info['largest_interval'] -= (PER_MOLECULE_STARTUP_TIME + PER_MOLECULE_GAP)
                req_durations['requests'].append(req_info)
            req_durations['duration'] = sum([req['duration'] for req in req_durations['requests']])
            errors = {}
        else:
            errors = serializer.errors

        return Response({'request_durations': req_durations,
                         'errors': errors})

    @list_route(methods=['post'])
    def cadence(self, request):
        expanded_requests = []
        for req in request.data.get('requests', []):
            if req.get('cadence'):
                cadence_request_serializer = CadenceRequestSerializer(data=req)
                if cadence_request_serializer.is_valid():
                    expanded_requests.extend(expand_cadence_request(cadence_request_serializer.validated_data))
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


class RequestViewSet(viewsets.ReadOnlyModelViewSet):
    metadata_class = RequestMetadata
    serializer_class = RequestSerializer
    filter_class = RequestFilter
    filter_backends = (
        filters.DjangoFilterBackend,
        filters.OrderingFilter
    )
    ordering = ('-id',)

    def get_queryset(self):
        if self.request.user.is_staff:
            return Request.objects.all()
        elif self.request.user.is_authenticated():
            return Request.objects.filter(
                user_request__proposal__in=self.request.user.proposal_set.all()
            )
        else:
            return Request.objects.none()

    @detail_route()
    def airmass(self, request, pk=None):
        return Response(get_airmasses_for_request_at_sites(self.get_object()))

    @detail_route()
    def telescope_states(self, request, pk=None):
        telescope_states = get_telescope_states_for_request(self.get_object())
        str_telescope_states = {str(k): v for k, v in telescope_states.items()}

        return Response(str_telescope_states)

    @detail_route()
    def blocks(self, request, pk=None):
        blocks = self.get_object().blocks
        if request.GET.get('canceled'):
            return Response([b for b in blocks if not b['canceled']])
        return Response(blocks)


class DraftUserRequestViewSet(viewsets.ModelViewSet):
    serializer_class = DraftUserRequestSerializer
    ordering = ('-modified',)

    def get_queryset(self):
        if self.request.user.is_authenticated():
            return DraftUserRequest.objects.filter(proposal__in=self.request.user.proposal_set.all())
        else:
            return DraftUserRequest.objects.none()
