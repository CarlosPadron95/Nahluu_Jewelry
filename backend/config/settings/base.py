"""
Configuración común a todos los entornos (desarrollo, tests y producción).

Ningún dato secreto se escribe aquí: todo lo sensible se lee de variables
de entorno (archivo .env en local, panel de Render en producción).
"""

from pathlib import Path

import environ

# Carpeta backend/ (donde está manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Lector de variables de entorno. Leemos el archivo .env si existe.
# "utf-8-sig" acepta también archivos guardados con BOM (lo hacen algunos
# programas de Windows, como el Bloc de notas o PowerShell 5).
env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env", encoding="utf-8-sig")


# --- Seguridad básica ---

# Clave secreta de Django. Es obligatoria: si falta, Django no arranca.
SECRET_KEY = env("DJANGO_SECRET_KEY")

# Por seguridad, DEBUG está apagado salvo que se active a propósito
DEBUG = env.bool("DJANGO_DEBUG", default=False)

# Dominios desde los que se puede acceder al backend
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])


# --- Aplicaciones ---

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
]

# Nuestras propias aplicaciones (catálogo, pedidos... irán aquí)
LOCAL_APPS = [
    "apps.core",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


# --- Middleware (el orden importa) ---

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise sirve los archivos estáticos del panel de administración
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # CORS tiene que ir antes de CommonMiddleware
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# --- Base de datos ---

# Se lee de una sola variable, por ejemplo:
# postgres://usuario:contraseña@localhost:5432/nahluu
DATABASES = {"default": env.db("DATABASE_URL")}

# Mantener abiertas las conexiones un rato para ir más rápido
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DATABASE_CONN_MAX_AGE", default=60)
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True

# Si la base de datos no responde en 5 segundos, damos error en vez de
# quedarnos esperando para siempre
DATABASES["default"].setdefault("OPTIONS", {})["connect_timeout"] = env.int(
    "DATABASE_CONNECT_TIMEOUT", default=5
)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- Contraseñas del panel de administración ---

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        # Pedimos contraseñas largas: al menos 12 caracteres
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --- Idiomas y zona horaria ---

LANGUAGE_CODE = "es"
LANGUAGES = [
    ("es", "Español"),
    ("en", "English"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = "Atlantic/Canary"
USE_I18N = True
USE_TZ = True


# --- Archivos estáticos (CSS y JS del panel de administración) ---

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# --- Panel de administración ---

# La ruta del panel se lee de una variable de entorno para que no sea
# la típica /admin/ en producción. Tiene que terminar en "/".
ADMIN_URL = env("DJANGO_ADMIN_URL", default="admin/")


# --- Django REST Framework (la API) ---

REST_FRAMEWORK = {
    # La API solo devuelve JSON
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    # Por defecto, nada es público: cada vista dice qué permite
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAdminUser"],
    # Límite de peticiones por visitante para frenar abusos
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": env("API_THROTTLE_ANON", default="120/minute"),
        "user": env("API_THROTTLE_USER", default="240/minute"),
    },
}


# --- CORS: qué webs pueden llamar a la API ---

# Solo nuestro frontend (en local, http://localhost:3000)
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])


# --- Cabeceras de seguridad comunes ---

X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"


# --- Registro de mensajes (logs) ---

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "{levelname} {asctime} {name}: {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {"handlers": ["console"], "level": env("DJANGO_LOG_LEVEL", default="INFO")},
}
