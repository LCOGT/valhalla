import django_filters
from rest_framework import filters
from valhalla.userrequests.models import UserRequest, Request


class UserRequestFilter(filters.FilterSet):
    created_after = django_filters.DateTimeFilter(name='created', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(name='created', lookup_expr='lte')
    state = django_filters.ChoiceFilter(choices=UserRequest.STATE_CHOICES)
    title = django_filters.CharFilter(name='group_id', lookup_expr='icontains')

    class Meta:
        model = UserRequest
        fields = (
            'id', 'submitter', 'proposal', 'title', 'observation_type', 'operator', 'ipp_value',
            'state', 'created_after', 'created_before'
        )


class RequestFilter(filters.FilterSet):
    class Meta:
        model = Request
        fields = ('state', 'fail_count')
