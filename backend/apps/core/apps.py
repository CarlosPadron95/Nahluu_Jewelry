from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Aplicación con utilidades comunes de la tienda (por ahora, el health check)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Núcleo"
