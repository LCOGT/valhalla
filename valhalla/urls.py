from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from rest_framework.routers import DefaultRouter
from django.conf.urls.static import static

from valhalla.userrequests.viewsets import RequestViewSet, UserRequestViewSet
from valhalla.userrequests.views import UserRequestListView
from valhalla.userrequests.views import telescope_states, telescope_availability
import valhalla.accounts.urls as accounts_urls
import valhalla.sciapplications.urls as sciapplications_urls
import valhalla.proposals.urls as proposals_urls

router = DefaultRouter()
router.register(r'requests', RequestViewSet, 'requests')
router.register(r'user_requests', UserRequestViewSet, 'user_requests')

urlpatterns = [
    url(r'^$', UserRequestListView.as_view(), name='index'),
    url(r'^accounts/', include(accounts_urls)),
    url(r'^api/', include(router.urls, namespace='api')),
    url(r'^proposals/', include(proposals_urls, namespace='proposals')),
    url(r'^apply/', include(sciapplications_urls, namespace='sciapplications')),
    url(r'^telescope_states/', telescope_states),
    url(r'^telescope_availability/', telescope_availability),
    url(r'^admin/', admin.site.urls),
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # Only available if debug is enabled
