from rest_framework import viewsets, filters
from rest_framework.decorators import list_route
from rest_framework.response import Response

from valhalla.userrequests.models import UserRequest, Request
from valhalla.userrequests.filters import UserRequestFilter, RequestFilter
from valhalla.userrequests.metadata import RequestMetadata
from valhalla.userrequests.serializers import RequestSerializer, UserRequestSerializer


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
        serializer = UserRequestSerializer(data=request.data)
        if serializer.is_valid():
            return Response('ok')
        else:
            return Response(serializer.errors)


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
