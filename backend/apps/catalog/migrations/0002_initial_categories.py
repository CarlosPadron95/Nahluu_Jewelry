"""
Migración de datos: crea las dos categorías con las que abre la tienda.

Así, al instalar el proyecto en cualquier sitio (tu ordenador, los tests
o Render), «Collares» y «Pendientes» ya existen sin crearlas a mano.
Si algún día se venden pulseras, se añaden desde el panel.
"""

from django.db import migrations

INITIAL_CATEGORIES = [
    {"slug": "collares", "name_es": "Collares", "name_en": "Necklaces", "position": 1},
    {"slug": "pendientes", "name_es": "Pendientes", "name_en": "Earrings", "position": 2},
]


def create_categories(apps, schema_editor):
    # En las migraciones se usa apps.get_model, no el modelo importado
    Category = apps.get_model("catalog", "Category")
    for data in INITIAL_CATEGORIES:
        Category.objects.get_or_create(slug=data["slug"], defaults=data)


def delete_categories(apps, schema_editor):
    # Para poder deshacer la migración
    Category = apps.get_model("catalog", "Category")
    slugs = [data["slug"] for data in INITIAL_CATEGORIES]
    Category.objects.filter(slug__in=slugs, products__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_categories, delete_categories),
    ]
