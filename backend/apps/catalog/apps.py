from django.apps import AppConfig


class CatalogConfig(AppConfig):
    """Catálogo de la tienda: categorías, colecciones, productos y sus fotos."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.catalog"
    verbose_name = "Catálogo"

    def ready(self):
        # Conectamos las señales que borran los archivos de las fotos viejas
        from . import signals  # noqa: F401
