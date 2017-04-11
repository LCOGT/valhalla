from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated, AllowAny

from valhalla.proposals.filters import SemesterFilter
from valhalla.proposals.models import Proposal, Semester
from valhalla.proposals.serializers import ProposalSerializer, SemesterSerialzer


class ProposalViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = ProposalSerializer
    filter_fields = '__all__'
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    ordering = ('-id',)

    def get_queryset(self):
        if self.request.user.is_staff:
            return Proposal.objects.all()
        else:
            return self.request.user.proposal_set.all()


class SemesterViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    serializer_class = SemesterSerialzer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter,)
    filter_class = SemesterFilter
    ordering = ('-id',)

    def get_queryset(self):
        return Semester.objects.filter(public=True)
