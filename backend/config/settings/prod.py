"""
Configuración de la tienda real (Render).

Todo lo que hay aquí endurece la seguridad. Para comprobarla:
    python manage.py check --deploy --settings=config.settings.prod
"""

from .base import *  # noqa: F403
from .base import STORAGES, env

DEBUG = False

# --- HTTPS obligatorio ---

# Render recibe la conexión segura y nos avisa con esta cabecera
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True

# Las cookies solo viajan por HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# HSTS: el navegador recordará que la web solo funciona con HTTPS
SECURE_HSTS_SECONDS = env.int("DJANGO_HSTS_SECONDS", default=60 * 60 * 24 * 365)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = env.bool("DJANGO_HSTS_PRELOAD", default=True)

# La sesión del panel de administración caduca tras 8 horas
SESSION_COOKIE_AGE = 60 * 60 * 8


# --- Fotos: en producción siempre van a Cloudinary ---

# Sin CLOUDINARY_URL, Django no arranca: el disco de Render se borra
# en cada despliegue y las fotos se perderían
CLOUDINARY_URL = env("CLOUDINARY_URL")
CLOUDINARY_FOLDER = env("CLOUDINARY_FOLDER", default="nahluu")
STORAGES["default"] = {
    "BACKEND": "apps.core.storage.CloudinaryStorage",
    "OPTIONS": {"cloudinary_url": CLOUDINARY_URL, "folder": CLOUDINARY_FOLDER},
}


# --- Verificación en dos pasos ---

# Nombre de la cuenta en la app de autenticación del móvil
OTP_TOTP_ISSUER = env("OTP_TOTP_ISSUER", default="Nahluu Jewelry")
