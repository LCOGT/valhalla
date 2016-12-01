from django.conf.urls import url

from valhalla.userrequests.views import RequestListView, RequestCreateView

urlpatterns = [
    url(r'^(?P<ur>\d+)/$', RequestListView.as_view(), name='list'),
    url(r'^create/$', RequestCreateView.as_view(), name='create')
]
