from django_filters.views import FilterView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404

from valhalla.userrequests.models import UserRequest, Request
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


class RequestListView(LoginRequiredMixin, FilterView):
    template_name = 'userrequests/request_list.html'
    model = Request
    paginate_by = 20

    def get_queryset(self):
        user_request = get_object_or_404(
            UserRequest,
            pk=self.kwargs['ur'],
            proposal__in=self.request.user.proposal_set.all()
        )
        return user_request.request_set.all()

    def get_context_data(self, filter=None, object_list=[]):
        context = super().get_context_data(filter=filter, object_list=object_list)
        context['userrequest'] = UserRequest.objects.get(pk=self.kwargs['ur'])
        return context
