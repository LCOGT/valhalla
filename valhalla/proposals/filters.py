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


class SemesterFilter(django_filters.FilterSet):
    semester_contains = django_filters.DateFilter(method='semester_contains_filter', label='Contains Date')

    def semester_contains_filter(self, queryset, name, value):
        return queryset.filter(start__lte=value, end__gte=value)

    class Meta:
        model = Semester
        fields = {'start': ['gte',],
                  'end': ['lte',],
                  'id': ['contains',],
                  }