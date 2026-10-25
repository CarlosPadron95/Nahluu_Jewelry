"""Datos de prueba que comparten los tests del catálogo (fixtures de pytest)."""

import pytest

from apps.catalog.models import Category, Product, ProductImage

from .utils import make_photo_file


@pytest.fixture
def necklaces(db):
    # La categoría la crea la migración 0002, así que ya existe
    return Category.objects.get(slug="collares")


@pytest.fixture
def draft_product(necklaces):
    """Un producto en borrador: solo con lo mínimo."""
    return Product.objects.create(
        name_es="Collar Marea",
        category=necklaces,
        price_cents=4550,
        stock=5,
    )


@pytest.fixture
def complete_product(draft_product):
    """Un producto con todo lo necesario para publicarlo (textos y una foto)."""
    draft_product.name_en = "Tide Necklace"
    draft_product.description_es = "Collar de plata 925 bañada en oro."
    draft_product.description_en = "925 silver necklace plated in gold."
    draft_product.save()
    ProductImage.objects.create(product=draft_product, image=make_photo_file())
    return draft_product
