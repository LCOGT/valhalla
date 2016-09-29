from rest_framework import viewsets, filters
from rest_framework.decorators import detail_route, list_route
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
    queryset = UserRequest.objects.all()

    @detail_route()
    def requests(self, request, pk=None):
        userrequest = self.get_object()
        us = RequestSerializer(userrequest.requests, many=True)
        return Response(us.data)

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
    queryset = Request.objects.all()
