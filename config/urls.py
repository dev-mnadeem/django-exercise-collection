"""Root URL configuration.

Media files are served by Django only while ``DEBUG`` is on; in production a
web server or object store fronts ``MEDIA_URL``.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("interview.core.urls")),
    path("admin/", admin.site.urls),
    path("inventory/", include("interview.inventory.urls")),
    path("orders/", include("interview.order.urls")),
    path("api-auth/", include("rest_framework.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
