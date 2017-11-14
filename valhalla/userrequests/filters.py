import django_filters
from valhalla.userrequests.models import UserRequest, Request, Location


class UserRequestFilter(django_filters.FilterSet):
    created_after = django_filters.DateTimeFilter(field_name='created', lookup_expr='gte', label='Submitted after')
    created_before = django_filters.DateTimeFilter(field_name='created', lookup_expr='lte', label='Submitted before')
    state = django_filters.ChoiceFilter(choices=UserRequest.STATE_CHOICES)
    title = django_filters.CharFilter(field_name='group_id', lookup_expr='icontains', label='Title contains')
    user = django_filters.CharFilter(field_name='submitter__username', lookup_expr='icontains', label='Username contains')
    exclude_state = django_filters.ChoiceFilter(field_name='state', choices=UserRequest.STATE_CHOICES, label='Exclude State', exclude=True)
    telescope_class = django_filters.ChoiceFilter(
        choices=Location.TELESCOPE_CLASSES, field_name='requests__location__telescope_class', distinct=True,
    )
    target = django_filters.CharFilter(
            field_name='requests__target__name', lookup_expr='icontains', label='Target name contains', distinct=True
    )
    modified_after = django_filters.DateTimeFilter(field_name='requests__modified', lookup_expr='gte', label='Modified After', distinct=True)
    modified_before = django_filters.DateTimeFilter(field_name='requests__modified', lookup_expr='lte', label='Modified Before', distinct=True)
    order = django_filters.OrderingFilter(
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
            'id', 'submitter', 'proposal', 'title', 'observation_type', 'operator', 'ipp_value',  'exclude_state',
            'state', 'created_after', 'created_before', 'user', 'modified_after', 'modified_before'
        )


class RequestFilter(django_filters.FilterSet):
    class Meta:
        model = Request
        fields = ('state', 'fail_count')
