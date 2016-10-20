from django_filters.views import FilterView
from rest_framework.response import Response
from datetime import datetime, timedelta
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


@api_view(['GET',])
def telescope_states(request):
    ''' Retrieves the telescope states for all telescopes between the start and end times
    :param request:
    :return:
    '''
    start = datetime.strptime(request.query_params.get('start', '2016-10-10 0:0:0'), '%Y-%m-%d %H:%M:%S')
    end = datetime.strptime(request.query_params.get('end', '2016-10-16 0:0:0'), '%Y-%m-%d %H:%M:%S')
    telescope_states = get_telescope_states(start, end)
    str_telescope_states = {str(k): v for k, v in telescope_states.items()}

    return Response(str_telescope_states)


@api_view(['GET',])
def telescope_availability(request):
    ''' Retrieves the nightly % availability of each telescope between the start and end times
    :param request:
    :return:
    '''
    start = datetime.strptime(request.query_params.get('start', '2016-10-10 0:0:0'), '%Y-%m-%d %H:%M:%S')
    end = datetime.strptime(request.query_params.get('end', '2016-10-16 0:0:0'), '%Y-%m-%d %H:%M:%S')
    telescope_availability = get_telescope_availability_per_day(start - timedelta(days=1), end + timedelta(days=1))
    str_telescope_availability = {str(k): v for k, v in telescope_availability.items()}

    return Response(str_telescope_availability)

