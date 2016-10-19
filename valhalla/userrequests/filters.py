import django_filters
from rest_framework import filters
from valhalla.userrequests.models import UserRequest, Request

USERREQUEST_STATE_FILTER_CHOICES = (('', '----------'),) + UserRequest.STATE_CHOICES


class UserRequestFilter(filters.FilterSet):
    created_after = django_filters.DateTimeFilter(name='created', lookup_type='gte')
    created_before = django_filters.DateTimeFilter(name='created', lookup_type='lte')
    state = django_filters.ChoiceFilter(choices=USERREQUEST_STATE_FILTER_CHOICES)
    title = django_filters.CharFilter(name='group_id', lookup_type='icontains')

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
