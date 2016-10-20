from django.conf.urls import url, include
from registration.backends.default.views import RegistrationView

from valhalla.accounts.forms import CustomRegistrationForm
from valhalla.accounts.views import UserUpdateView
urlpatterns = [
    url(r'^register/$', RegistrationView.as_view(form_class=CustomRegistrationForm), name='registration_register'),
    url(r'^profile/$', UserUpdateView.as_view(), name='profile'),
    url(r'', include('registration.backends.default.urls')),
]
