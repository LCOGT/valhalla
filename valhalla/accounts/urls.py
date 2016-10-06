from django.conf.urls import url, include
from valhalla.accounts.forms import CustomRegistrationForm
from registration.backends.default.views import RegistrationView

urlpatterns = [
    url(r'^register/$', RegistrationView.as_view(form_class=CustomRegistrationForm), name='registration_register'),
    url(r'', include('registration.backends.default.urls')),
]
