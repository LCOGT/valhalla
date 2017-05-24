import django_filters
from django.utils import timezone
from dateutil.parser import parse
from valhalla.proposals.models import Semester, Proposal


class ProposalFilter(django_filters.FilterSet):
    semester = django_filters.ModelChoiceFilter(
        label="Semester", distinct=True, queryset=Semester.objects.filter(public=True).order_by('-start')
    )
    active = django_filters.ChoiceFilter(choices=((False, 'Inactive'), (True, 'Active')), empty_label='All')

    class Meta:
        model = Proposal
        fields = ('active', 'semester', 'id', 'tac_rank', 'tac_priority', 'public', 'title')


class SemesterFilter(django_filters.FilterSet):
    semester_contains = django_filters.CharFilter(method='semester_contains_filter', label='Contains Date')

    def semester_contains_filter(self, queryset, name, value):
        try:
            date_value = parse(value)
            date_value = date_value.replace(tzinfo=timezone.utc)
            return queryset.filter(start__lte=date_value, end__gte=date_value)
        except ValueError:
            return queryset

    class Meta:
        model = Semester
        fields = {
            'start': ['gte'],
            'end': ['lte'],
            'id': ['contains'],
        }
