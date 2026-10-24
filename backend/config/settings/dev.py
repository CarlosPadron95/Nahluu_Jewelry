"""Configuración para programar en local."""

from .base import *  # noqa: F403
from .base import REST_FRAMEWORK, env

# En local queremos ver los errores con detalle
DEBUG = env.bool("DJANGO_DEBUG", default=True)

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# El frontend de Next.js corre en el puerto 3000
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=["http://localhost:3000"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=["http://localhost:3000"])

# En local también se puede ver la API en el navegador (pantalla de DRF)
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
]

# WhiteNoise en modo desarrollo: busca los estáticos al vuelo,
# así no hace falta ejecutar collectstatic en local
WHITENOISE_AUTOREFRESH = True
WHITENOISE_USE_FINDERS = True
