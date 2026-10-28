"""
Configuración para usar NUESTRO panel de administración en vez del de Django.

Este archivo solo tiene la configuración (y apunta al panel con un texto):
si importáramos aquí el panel directamente, Django daría error al arrancar,
porque aún no habría cargado los modelos de usuarios.
"""

from django.contrib.admin.apps import AdminConfig


class NahluuAdminConfig(AdminConfig):
    # Panel con verificación en dos pasos (ver apps/core/admin_site.py)
    default_site = "apps.core.admin_site.NahluuAdminSite"
