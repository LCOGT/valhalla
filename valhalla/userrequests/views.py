from django_filters.views import FilterView
from rest_framework.response import Response
from django.http import HttpResponseBadRequest
from django.utils import timezone
from dateutil.parser import parse
from rest_framework.decorators import api_view
from valhalla.common.telescope_states import get_telescope_states, get_telescope_availability_per_day

from valhalla.userrequests.models import UserRequest
from valhalla.userrequests.filters import UserRequestFilter


class UserRequestListView(FilterView):
    filterset_class = UserRequestFilter
    template_name = 'userrequests/userrequest_list.html'
    paginate_by = 20

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return UserRequest.objects.filter(proposal__in=self.request.user.proposal_set.all())
        else:
            return UserRequest.objects.none()


@api_view(['GET'])
def telescope_states(request):
    ''' Retrieves the telescope states for all telescopes between the start and end times
    '''
    try:
        start = parse(request.query_params.get('start', '2016-10-10T0:0:0'))
        if not start.tzinfo:
            start = start.replace(tzinfo=timezone.utc)
        end = parse(request.query_params.get('end', '2016-10-16T0:0:0'))
        if not end.tzinfo:
            end = end.replace(tzinfo=timezone.utc)
    except ValueError as e:
        return HttpResponseBadRequest(str(e))
    sites = request.query_params.getlist('site', None)
    telescopes = request.query_params.getlist('telescope', None)
    telescope_states = get_telescope_states(start, end, sites=sites, telescopes=telescopes)
    str_telescope_states = {str(k): v for k, v in telescope_states.items()}

    return Response(str_telescope_states)


@api_view(['GET'])
def telescope_availability(request):
    ''' Retrieves the nightly % availability of each telescope between the start and end times
    '''
    try:
        start = parse(request.query_params.get('start', '2016-10-10T0:0:0'))
        if not start.tzinfo:
            start = start.replace(tzinfo=timezone.utc)
        end = parse(request.query_params.get('end', '2016-10-16T0:0:0'))
        if not end.tzinfo:
            end = end.replace(tzinfo=timezone.utc)
    except ValueError as e:
        return HttpResponseBadRequest(str(e))
    sites = request.query_params.getlist('sites', None)
    telescopes = request.query_params.getlist('telescope', None)
    telescope_availability = get_telescope_availability_per_day(start,
                                                                end,
                                                                sites=sites,
                                                                telescopes=telescopes)
    str_telescope_availability = {str(k): v for k, v in telescope_availability.items()}

    return Response(str_telescope_availability)
