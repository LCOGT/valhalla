from django.conf.urls import url

from valhalla.userrequests.views import RequestListView

urlpatterns = [
    url(r'^(?P<ur>\d+)/$', RequestListView.as_view(), name='request-list'),
]
