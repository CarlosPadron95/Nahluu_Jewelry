from django.apps import AppConfig
from django.db.models.signals import post_migrate


class CoreConfig(AppConfig):
    """Utilidades comunes de la tienda: health check, dinero, idiomas, panel seguro..."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Núcleo"

    def ready(self):
        # Después de cada migrate, creamos o actualizamos el grupo "Equipo de la tienda"
        from .groups import ensure_shop_staff_group

        post_migrate.connect(ensure_shop_staff_group, sender=self)
