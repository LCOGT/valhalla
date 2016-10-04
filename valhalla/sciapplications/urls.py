from django.conf.urls import url

from valhalla.sciapplications.views import (
    SciApplicationCreateView, SciApplicationUpdateView, SciApplicationIndexView
)

urlpatterns = [
    url(r'^$', SciApplicationIndexView.as_view(), name='index'),
    url(r'^create/(?P<call>\d+)/$', SciApplicationCreateView.as_view(), name='create'),
    url(r'^update/(?P<pk>\d+)/$', SciApplicationUpdateView.as_view(), name='update')
]
