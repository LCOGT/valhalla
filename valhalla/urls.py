from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic import TemplateView

import valhalla.accounts.urls as accounts_urls

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='index.html'), name='index'),
    url(r'^accounts/', include(accounts_urls)),
    url(r'^admin/', admin.site.urls),
]
