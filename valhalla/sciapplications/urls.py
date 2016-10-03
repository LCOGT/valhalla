from django.conf.urls import url
from django.views.generic import TemplateView

from valhalla.sciapplications.views import SciApplicationCreateView, SciApplicationUpdateView

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='sciapplications/index.html'), name='index'),
    url(r'^create/(?P<semester>\w+)/(?P<type>\w+)/$', SciApplicationCreateView.as_view(), name='create'),
    url(r'^update/(?P<pk>\d+)/$', SciApplicationUpdateView.as_view(), name='update')
]
