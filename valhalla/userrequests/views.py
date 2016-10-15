from django_filters.views import FilterView

from valhalla.userrequests.models import UserRequest
from valhalla.userrequests.filters import UserRequestFilter


class UserRequestListView(FilterView):
    filterset_class = UserRequestFilter
    template_name = 'userrequests/userrequest_list.html'
    paginate_by = 20

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return UserRequest.objects.filter(submitter=self.request.user)
        else:
            return UserRequest.objects.none()
