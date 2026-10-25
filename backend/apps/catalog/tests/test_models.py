"""Tests de los modelos del catálogo."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.catalog.models import Category, Product


@pytest.mark.django_db
def test_la_tienda_abre_con_collares_y_pendientes():
    # Las crea la migración 0002_initial_categories
    slugs = list(Category.objects.values_list("slug", flat=True))

    assert slugs == ["collares", "pendientes"]


def test_el_producto_se_muestra_con_su_nombre(draft_product):
    assert str(draft_product) == "Collar Marea"


def test_la_direccion_web_se_crea_sola_con_el_nombre(draft_product):
    assert draft_product.slug == "collar-marea"


def test_el_precio_se_muestra_en_euros(draft_product):
    assert draft_product.price_display == "45,50\u00a0€"


def test_la_base_de_datos_no_acepta_precios_de_cero(necklaces):
    # Aunque alguien se salte el formulario, la base de datos lo impide
    with pytest.raises(IntegrityError):
        Product.objects.create(name_es="Gratis", category=necklaces, price_cents=0)


@pytest.mark.parametrize(
    ("stock", "is_new", "labels"),
    [
        (10, False, []),
        (3, False, ["Últimas unidades"]),
        (1, False, ["Últimas unidades"]),
        (0, False, ["Agotado"]),
        (10, True, ["Nuevo"]),
        (0, True, ["Nuevo", "Agotado"]),
    ],
)
def test_etiquetas_de_la_tarjeta(draft_product, stock, is_new, labels):
    draft_product.stock = stock
    draft_product.is_new = is_new

    assert draft_product.labels == labels


def test_un_borrador_se_puede_guardar_incompleto(draft_product):
    # No debe lanzar ningún error
    draft_product.full_clean()


def test_para_publicar_hacen_falta_los_textos_en_los_dos_idiomas(draft_product):
    draft_product.is_active = True

    with pytest.raises(ValidationError) as error:
        draft_product.full_clean()

    assert set(error.value.message_dict) == {"name_en", "description_es", "description_en"}


def test_un_producto_completo_se_puede_publicar(complete_product):
    complete_product.is_active = True

    complete_product.full_clean()
    assert complete_product.publishing_problems() == []


def test_lo_que_falta_para_publicar_un_borrador(draft_product):
    problems = draft_product.publishing_problems()

    assert "falta al menos una foto" in problems
    assert "falta «nombre (inglés)»" in problems


def test_la_tienda_solo_ve_los_productos_publicados(draft_product, complete_product, necklaces):
    hidden = Product.objects.create(name_es="Oculto", category=necklaces, price_cents=1000)
    complete_product.is_active = True
    complete_product.save()

    published = list(Product.objects.published())

    assert complete_product in published
    assert hidden not in published


def test_no_se_puede_borrar_una_categoria_con_productos(draft_product, necklaces):
    from django.db.models import ProtectedError

    with pytest.raises(ProtectedError):
        necklaces.delete()
