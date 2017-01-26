from rest_framework import viewsets, filters
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response

from valhalla.userrequests.models import UserRequest, Request, DraftUserRequest
from valhalla.userrequests.filters import UserRequestFilter, RequestFilter
from valhalla.userrequests.metadata import RequestMetadata
from valhalla.userrequests.serializers import RequestSerializer, UserRequestSerializer, DraftUserRequestSerializer
from valhalla.userrequests.duration_utils import get_request_duration
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
        if serializer.is_valid():
            duration = sum([get_request_duration(req) for req in serializer.validated_data['requests']])
            errors = []
        else:
            errors = serializer.errors
            duration = 0
        return Response({'duration': duration, 'errors': errors})


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
