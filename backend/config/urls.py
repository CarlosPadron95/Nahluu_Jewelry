"""Rutas principales del backend."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

# Textos del panel de administración
admin.site.site_header = "Nahluu Jewelry · Administración"
admin.site.site_title = "Nahluu Jewelry"
admin.site.index_title = "Panel de la tienda"

urlpatterns = [
    # El panel de administración vive en una ruta configurable (ver ADMIN_URL)
    path(settings.ADMIN_URL, admin.site.urls),
    # Toda la API empieza por /api/
    path("api/", include("apps.core.urls")),
]

# En local, Django sirve las fotos subidas (en producción las sirve Cloudinary)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
