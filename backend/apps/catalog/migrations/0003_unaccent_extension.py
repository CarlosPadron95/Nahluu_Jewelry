"""
Activa la extensión unaccent de PostgreSQL.

Permite buscar sin tener en cuenta las tildes: «corazon» encuentra «Corazón».
Es una extensión "de confianza": no hacen falta permisos de administrador
de la base de datos para activarla (también funciona en Render).
"""

from django.contrib.postgres.operations import UnaccentExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0002_initial_categories"),
    ]

    operations = [
        UnaccentExtension(),
    ]
