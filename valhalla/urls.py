from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from rest_framework.routers import DefaultRouter
from django.conf.urls.static import static

from valhalla.userrequests.viewsets import RequestViewSet, UserRequestViewSet, DraftUserRequestViewSet
from valhalla.userrequests.views import TelescopeStatesView, TelescopeAvailabilityView, AirmassView
from valhalla.userrequests.views import UserRequestListView, InstrumentsInformationView
from valhalla.accounts.views import ProfileApiView
import valhalla.accounts.urls as accounts_urls
import valhalla.sciapplications.urls as sciapplications_urls
import valhalla.proposals.urls as proposals_urls
import valhalla.userrequests.urls as userrequest_urls

router = DefaultRouter()
router.register(r'requests', RequestViewSet, 'requests')
router.register(r'user_requests', UserRequestViewSet, 'user_requests')
router.register(r'drafts', DraftUserRequestViewSet, 'drafts')

api_urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^telescope_states/', TelescopeStatesView.as_view(), name='telescope_states'),
    url(r'^telescope_availability/', TelescopeAvailabilityView.as_view(), name='telescope_availability'),
    url(r'profile/', ProfileApiView.as_view(), name='profile'),
    url(r'airmass/', AirmassView.as_view(), name='airmass'),
    url(r'instruments/', InstrumentsInformationView.as_view(), name='instruments_information'),
]

urlpatterns = [
    url(r'^', include(userrequest_urls, namespace='userrequests')),
    url(r'^accounts/', include(accounts_urls)),
    url(r'^api/', include(api_urlpatterns, namespace='api')),
    url(r'^proposals/', include(proposals_urls, namespace='proposals')),
    url(r'^apply/', include(sciapplications_urls, namespace='sciapplications')),
    url(r'^telescope_states/', TelescopeStatesView.as_view(), name='telescope_states'),
    url(r'^telescope_availability/', TelescopeAvailabilityView.as_view(), name='telescope_availability'),
    url(r'^admin/', admin.site.urls),
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # Only available if debug is enabled
