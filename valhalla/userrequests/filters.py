import django_filters
from rest_framework import filters
from valhalla.userrequests.models import UserRequest, Request


class UserRequestFilter(filters.FilterSet):
    created_after = django_filters.DateTimeFilter(name='created', lookup_type='gte')
    created_before = django_filters.DateTimeFilter(name='created', lookup_type='lte')

    class Meta:
        model = UserRequest
        fields = (
            'id', 'submitter', 'proposal', 'group_id', 'observation_type', 'operator', 'ipp_value',
            'state', 'created_after', 'created_before'
        )


class RequestFilter(filters.FilterSet):
    class Meta:
        model = Request
        fields = ('state', 'fail_count')
