from django.conf.urls import url

from valhalla.sciapplications.views import (
    SciApplicationCreateView, SciApplicationUpdateView, SciApplicationIndexView,
    SciApplicationDetailView, SciApplicationDeleteView
)

urlpatterns = [
    url(r'^$', SciApplicationIndexView.as_view(), name='index'),
    url(r'^(?P<pk>\d+)/$', SciApplicationDetailView.as_view(), name='detail'),
    url(r'^create/(?P<call>\d+)/$', SciApplicationCreateView.as_view(), name='create'),
    url(r'^update/(?P<pk>\d+)/$', SciApplicationUpdateView.as_view(), name='update'),
    url(r'^delete/(?P<pk>\d+)/$', SciApplicationDeleteView.as_view(), name='delete'),

]
