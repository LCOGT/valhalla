import django_filters
from rest_framework import filters
from valhalla.userrequests.models import UserRequest, Request, Location


class UserRequestFilter(filters.FilterSet):
    created_after = django_filters.DateTimeFilter(name='created', lookup_expr='gte', label='Submitted after')
    created_before = django_filters.DateTimeFilter(name='created', lookup_expr='lte', label='Submitted before')
    state = django_filters.ChoiceFilter(choices=UserRequest.STATE_CHOICES)
    title = django_filters.CharFilter(name='group_id', lookup_expr='icontains', label='Title contains')
    user = django_filters.CharFilter(name='submitter__username', lookup_expr='icontains', label='Username contains')
    telescope_class = django_filters.ChoiceFilter(
        choices=Location.TELESCOPE_CLASSES, name='requests__location__telescope_class'
    )
    target = django_filters.CharFilter(
            name='requests__target__name', lookup_expr='icontains', label='Target name contains'
    )
    o = django_filters.OrderingFilter(
        fields=(
            ('group_id', 'title'),
            ('modified', 'modified'),
            ('created', 'created'),
            ('requests__windows__end', 'end')
        ),
        field_labels={
            'requests__windows__end': 'End of window',
            'modified': 'Last Update'
        }
    )

    class Meta:
        model = UserRequest
        fields = (
            'id', 'submitter', 'proposal', 'title', 'observation_type', 'operator', 'ipp_value',
            'state', 'created_after', 'created_before', 'user'
        )


class RequestFilter(filters.FilterSet):
    class Meta:
        model = Request
        fields = ('state', 'fail_count')
