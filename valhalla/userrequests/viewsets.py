from rest_framework import viewsets, filters
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from dateutil.parser import parse
import logging

from valhalla.proposals.models import Proposal, Semester, TimeAllocation
from valhalla.userrequests.models import UserRequest, Request, DraftUserRequest
from valhalla.userrequests.filters import UserRequestFilter, RequestFilter
from valhalla.userrequests.cadence import expand_cadence_request
from valhalla.userrequests.serializers import RequestSerializer, UserRequestSerializer
from valhalla.userrequests.serializers import DraftUserRequestSerializer, CadenceRequestSerializer
from valhalla.userrequests.duration_utils import (get_request_duration_dict, get_max_ipp_for_userrequest,
                                                  OVERHEAD_ALLOWANCE)
from valhalla.userrequests.state_changes import InvalidStateChange, TERMINAL_STATES
from valhalla.userrequests.request_utils import (get_airmasses_for_request_at_sites,
                                                 get_telescope_states_for_request)
logger = logging.getLogger(__name__)


class UserRequestViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    http_method_names = ['get', 'post', 'head', 'options']
    serializer_class = UserRequestSerializer
    filter_class = UserRequestFilter
    filter_backends = (
        filters.OrderingFilter,
        DjangoFilterBackend
    )
    ordering = ('-id',)

    def get_throttles(self):
        actions_to_throttle = ['cancel', 'validate']
        if self.action in actions_to_throttle:
            self.throttle_scope = 'userrequests.' + self.action
        return super().get_throttles()

    def get_queryset(self):
        if self.request.user.is_staff:
            qs = UserRequest.objects.all()
        elif self.request.user.is_authenticated:
            qs = UserRequest.objects.filter(
                proposal__in=self.request.user.proposal_set.all()
            )
        else:
            qs = UserRequest.objects.filter(proposal__in=Proposal.objects.filter(public=True))
        return qs.prefetch_related(
            'requests', 'requests__windows', 'requests__molecules', 'requests__constraints',
            'requests__target', 'requests__location'
        )

    @list_route(methods=['get'], permission_classes=(IsAdminUser,))
    def schedulable_requests(self, request):
        '''
            Gets the set of schedulable User requests for the scheduler, should be called right after isDirty finishes
            Needs a start and end time specified as the range of time to get requests in. Usually this is the entire
            semester for a scheduling run.
        '''
        current_semester = Semester.current_semesters().first()
        start = parse(request.query_params.get('start', str(current_semester.start))).replace(tzinfo=timezone.utc)
        end = parse(request.query_params.get('end', str(current_semester.end))).replace(tzinfo=timezone.utc)

        # Schedulable requests are not in a terminal state, are part of an active proposal,
        # and have a window within this semester
        queryset = UserRequest.objects.exclude(state__in=TERMINAL_STATES).filter(
            requests__windows__start__lte=end, requests__windows__start__gte=start,
            proposal__active=True).prefetch_related('requests', 'requests__windows', 'requests__target', 'proposal',
                                                    'proposal__timeallocation_set', 'requests__molecules',
                                                    'requests__location', 'requests__constraints').distinct()

        # queryset now contains all the schedulable URs and their associated requests and data
        # Check that each request time available in its proposal still
        ur_data = []
        tas = {}
        for ur in queryset.all():
            total_duration_dict = ur.total_duration
            for tak, duration in total_duration_dict.items():
                if (tak, ur.proposal.id) in tas:
                    time_allocation = tas[(tak, ur.proposal.id)]
                else:
                    time_allocation = TimeAllocation.objects.get(
                        semester=tak.semester,
                        instrument_name=tak.instrument_name,
                        telescope_class=tak.telescope_class,
                        proposal=ur.proposal.id,
                    )
                    tas[(tak, ur.proposal.id)] = time_allocation
                if ur.observation_type == UserRequest.NORMAL:
                    time_left = time_allocation.std_allocation - time_allocation.std_time_used
                else:
                    time_left = time_allocation.too_allocation - time_allocation.too_time_used
                if time_left * OVERHEAD_ALLOWANCE >= (duration / 3600.0):
                    serialized_ur = UserRequestSerializer(ur)
                    ur_data.append(serialized_ur.data)
                    break
                else:
                    logger.warning(
                        'not enough time left {0} in proposal {1} for ur {2} of duration {3}, skipping'.format(
                            time_left, ur.proposal.id, ur.id, (duration / 3600.0)
                        )
                    )

        return Response(ur_data)

    @detail_route(methods=['post'])
    def cancel(self, request, pk=None):
        ur = self.get_object()
        try:
            ur.state = 'CANCELED'
            ur.save()
        except InvalidStateChange as exc:
            return Response({'errors': [str(exc)]}, status=400)
        return Response(UserRequestSerializer(ur).data)

    @list_route(methods=['post'])
    def validate(self, request):
        serializer = UserRequestSerializer(data=request.data, context={'request': request})
        req_durations = {}
        if serializer.is_valid():
            req_durations = get_request_duration_dict(serializer.validated_data['requests'])
            errors = {}
        else:
            errors = serializer.errors

        return Response({'request_durations': req_durations,
                         'errors': errors})

    @list_route(methods=['post'])
    def max_allowable_ipp(self, request):
        # change requested ipp to 1 because we want it to always pass the serializers ipp check
        request.data['ipp_value'] = 1.0
        serializer = UserRequestSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            ipp_dict = get_max_ipp_for_userrequest(serializer.validated_data)
            return Response(ipp_dict)
        else:
            return Response({'errors': serializer.errors})

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
        ret_data = request.data.copy()
        ret_data['requests'] = expanded_requests

        if(len(ret_data['requests']) > 1):
            ret_data['operator'] = 'MANY'
        ur_serializer = UserRequestSerializer(data=ret_data, context={'request': request})
        if not ur_serializer.is_valid():
            return Response(ur_serializer.errors, status=400)
        return Response(ret_data)


class RequestViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = RequestSerializer
    filter_class = RequestFilter
    filter_backends = (
        filters.OrderingFilter,
        DjangoFilterBackend
    )
    ordering = ('-id',)
    ordering_fields = ('id', 'state', 'fail_count')

    def get_queryset(self):
        if self.request.user.is_staff:
            return Request.objects.all()
        elif self.request.user.is_authenticated:
            return Request.objects.filter(
                user_request__proposal__in=self.request.user.proposal_set.all()
            )
        else:
            return Request.objects.filter(user_request__proposal__in=Proposal.objects.filter(public=True))

    @detail_route()
    def airmass(self, request, pk=None):
        return Response(get_airmasses_for_request_at_sites(self.get_object().as_dict))

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
        if self.request.user.is_authenticated:
            return DraftUserRequest.objects.filter(proposal__in=self.request.user.proposal_set.all())
        else:
            return DraftUserRequest.objects.none()
