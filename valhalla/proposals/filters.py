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
