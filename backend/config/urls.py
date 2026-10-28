"""Rutas principales del backend."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # El panel de administración (con verificación en dos pasos, ver apps/core/admin_site.py)
    # vive en una ruta configurable (ver ADMIN_URL)
    path(settings.ADMIN_URL, admin.site.urls),
    # Toda la API empieza por /api/
    path("api/", include("apps.core.urls")),
    # API pública del catálogo (solo lectura)
    path("api/catalog/", include("apps.catalog.urls")),
]

# En local sin Cloudinary, Django sirve las fotos de backend/media/
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
