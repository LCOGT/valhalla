from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from django.views.generic import TemplateView
from django.conf.urls.static import static

import valhalla.accounts.urls as accounts_urls
import valhalla.sciapplications.urls as sciapplications_urls

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='index.html'), name='index'),
    url(r'^accounts/', include(accounts_urls)),
    url(r'^apply/', include(sciapplications_urls, namespace='sciapplications')),
    url(r'^admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # Only available if debug is enabled
