"""Configuración para los tests automáticos (pytest y GitHub Actions)."""

from .base import *  # noqa: F403
from .base import REST_FRAMEWORK

DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost"]

# Un cifrado de contraseñas muy rápido: los tests van mucho más deprisa
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# En los tests no queremos que el límite de peticiones nos bloquee
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []

# Los estáticos sin compresión, para no tener que ejecutar collectstatic
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# WhiteNoise en modo desarrollo: busca los estáticos al vuelo
WHITENOISE_AUTOREFRESH = True
WHITENOISE_USE_FINDERS = True
