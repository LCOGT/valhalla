from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter

from valhalla.userrequests.viewsets import RequestViewSet, UserRequestViewSet
import valhalla.accounts.urls as accounts_urls

router = DefaultRouter()
router.register(r'requests', RequestViewSet, 'requests')
router.register(r'user_requests', UserRequestViewSet, 'user_requests')

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='index.html'), name='index'),
    url(r'^accounts/', include(accounts_urls)),
    url(r'^api/', include(router.urls, namespace='api')),
    url(r'^admin/', admin.site.urls),
]
