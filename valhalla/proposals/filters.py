import django_filters

from valhalla.proposals.models import Semester, Proposal


class ProposalFilter(django_filters.FilterSet):
    semester = django_filters.ModelChoiceFilter(
        label="Semester", distinct=True, queryset=Semester.objects.filter(public=True).order_by('-start')
    )
    active = django_filters.ChoiceFilter(choices=((0, 'Inactive'), (1, 'Active')), empty_label='All')

    class Meta:
        model = Proposal
        fields = ('active', 'semester')


class WithinDatesFilter(django_filters.DateFilter):

    def __init__(self, start_field, end_field, **kwargs):
        super(WithinDatesFilter, self).__init__(**kwargs)
        self.start_field = start_field
        self.end_field = end_field

    def filter(self, queryset, value):
        if value:
            query_filters = {'{}__lte'.format(self.start_field): value,
                             '{}__gte'.format(self.end_field): value}
            queryset = queryset.filter(**query_filters)

        return queryset


class SemesterFilter(django_filters.FilterSet):
    semester_contains = WithinDatesFilter(start_field='start', end_field='end', label='Contains Date')

    class Meta:
        model = Semester
        fields = {'start': ['gte',],
                  'end': ['lte',],
                  'id': ['contains',],
                  'semester_contains': ['contains',],
                  }