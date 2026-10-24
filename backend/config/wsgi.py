"""Arranque del backend en producción (Gunicorn usa este archivo)."""

import os

from django.core.wsgi import get_wsgi_application

# En el servidor, por defecto, la configuración de producción
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

application = get_wsgi_application()
