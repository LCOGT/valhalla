from django.conf.urls import url, include
from registration.backends.default.views import RegistrationView

from valhalla.accounts.forms import CustomRegistrationForm
from valhalla.accounts.views import UserUpdateView, RevokeAPITokenView

urlpatterns = [
    url(r'^register/$', RegistrationView.as_view(form_class=CustomRegistrationForm), name='registration_register'),
    url(r'^profile/$', UserUpdateView.as_view(), name='profile'),
    url(r'^revoketoken/$', RevokeAPITokenView.as_view(), name='revoke-api-token'),
    url(r'', include('registration.backends.default.urls')),
]
