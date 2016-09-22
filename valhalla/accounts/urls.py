from django.conf.urls import url, include
from valhalla.accounts.views import CustomRegistrationView

urlpatterns = [
    url(r'^register/$', CustomRegistrationView.as_view(), name='registration_register'),
    url(r'', include('registration.backends.default.urls')),
]
