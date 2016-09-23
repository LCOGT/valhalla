from django.conf.urls import url
from valhalla.sciapplications.views import SciApplicationView

urlpatterns = [
    url(r'^create/(?P<semester>.+)/(?P<app_type>.+)/$', SciApplicationView.as_view(), name='create'),
]
