from django.conf.urls import url

from valhalla.userrequests.views import UserRequestListView, RequestDetailView, RequestCreateView, UserRequestDetailView

urlpatterns = [
    url(r'^$', UserRequestListView.as_view(), name='list'),
    url(r'^userrequests/(?P<pk>\d+)/$', UserRequestDetailView.as_view(), name='detail'),
    url(r'^requests/(?P<pk>\d+)/$', RequestDetailView.as_view(), name='request-detail'),
    url(r'^create/$', RequestCreateView.as_view(), name='create')
]
