"""
Grupo de permisos para el equipo de la tienda (por ejemplo, Andrea).

Principio de "mínimo privilegio": cada persona solo puede hacer lo que
necesita. El equipo de la tienda gestiona el catálogo (y más adelante
los pedidos), pero NO puede crear usuarios, cambiar permisos ni tocar
la seguridad del panel. Eso queda solo para el superusuario.

El grupo se crea y se actualiza solo cada vez que se ejecuta
"python manage.py migrate". Sus permisos se definen AQUÍ, en el código:
si se cambian a mano en el panel, el siguiente migrate los deja como aquí.
"""

from django.apps import apps as global_apps
from django.contrib.auth.management import create_permissions
from django.db import DEFAULT_DB_ALIAS

SHOP_STAFF_GROUP = "Equipo de la tienda"

# Aplicaciones que el equipo puede gestionar (ver, añadir, cambiar y borrar)
SHOP_STAFF_APPS = ["catalog"]


def ensure_shop_staff_group(using=DEFAULT_DB_ALIAS, **kwargs):
    """Crea el grupo si no existe y le da los permisos de SHOP_STAFF_APPS."""
    from django.contrib.auth.models import Group, Permission

    # Nos aseguramos de que los permisos ya existen (en una base de datos
    # nueva, Django los crea al final del migrate y puede que aún no estén)
    for app_label in SHOP_STAFF_APPS:
        create_permissions(global_apps.get_app_config(app_label), verbosity=0, using=using)

    group, _created = Group.objects.using(using).get_or_create(name=SHOP_STAFF_GROUP)
    permissions = Permission.objects.using(using).filter(
        content_type__app_label__in=SHOP_STAFF_APPS
    )
    group.permissions.set(permissions)
