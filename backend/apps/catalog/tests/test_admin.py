"""
Tests del panel de administración del catálogo.

admin_client es un navegador de pruebas con un superusuario ya
identificado (lo da pytest-django).
"""

import pytest
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.urls import reverse

from apps.catalog.models import Product

from .utils import make_photo_file


def product_form_data(category, **changes):
    """Datos del formulario de producto, como los enviaría el navegador."""
    data = {
        "name_es": "Pendientes Espuma",
        "slug": "pendientes-espuma",
        "description_es": "Pendientes de plata 925 bañada en oro.",
        "details_es": "",
        "name_en": "Sea Foam Earrings",
        "description_en": "925 silver earrings plated in gold.",
        "details_en": "",
        "category": category.pk,
        "collection": "",
        "position": "0",
        "price": "39,90",  # con coma, como se escribe en España
        "stock": "4",
        "weight_grams": "",
        # Datos de control del bloque de fotos (lo que Django llama "formset")
        "images-TOTAL_FORMS": "1",
        "images-INITIAL_FORMS": "0",
        "images-MIN_NUM_FORMS": "0",
        "images-MAX_NUM_FORMS": "1000",
        "images-0-alt_es": "",
        "images-0-alt_en": "",
        "images-0-position": "0",
    }
    data.update(changes)
    return data


@pytest.mark.parametrize(
    "url_name", ["admin:catalog_product_changelist", "admin:catalog_product_add"]
)
def test_las_pantallas_de_productos_cargan(admin_client, complete_product, url_name):
    response = admin_client.get(reverse(url_name))

    assert response.status_code == 200


def test_la_ficha_muestra_el_precio_en_euros(admin_client, complete_product):
    url = reverse("admin:catalog_product_change", args=[complete_product.pk])

    response = admin_client.get(url)

    assert response.status_code == 200
    assert 'value="45,50"' in response.content.decode()


@pytest.mark.parametrize(
    "url_name", ["admin:catalog_collection_changelist", "admin:catalog_category_changelist"]
)
def test_las_pantallas_de_colecciones_y_categorias_cargan(admin_client, url_name):
    response = admin_client.get(reverse(url_name))

    assert response.status_code == 200


def test_crear_un_producto_con_foto_desde_el_panel(admin_client, necklaces):
    data = product_form_data(necklaces, **{"images-0-image": make_photo_file()})

    response = admin_client.post(reverse("admin:catalog_product_add"), data)

    assert response.status_code == 302  # redirige a la lista: se ha guardado
    product = Product.objects.get(slug="pendientes-espuma")
    assert product.price_cents == 3990
    assert product.images.count() == 1


def test_no_se_puede_publicar_sin_fotos(admin_client, necklaces):
    data = product_form_data(necklaces, is_active="on")

    response = admin_client.post(reverse("admin:catalog_product_add"), data)

    assert response.status_code == 200  # vuelve a mostrar el formulario con el error
    assert "Un producto publicado necesita al menos una foto." in response.content.decode()
    assert not Product.objects.exists()


def test_no_se_puede_publicar_sin_los_textos_en_ingles(admin_client, necklaces):
    data = product_form_data(
        necklaces,
        is_active="on",
        name_en="",
        **{"images-0-image": make_photo_file()},
    )

    response = admin_client.post(reverse("admin:catalog_product_add"), data)

    assert response.status_code == 200
    assert "Obligatorio para publicar el producto." in response.content.decode()
    assert not Product.objects.exists()


def test_el_precio_no_puede_ser_cero(admin_client, necklaces):
    data = product_form_data(necklaces, price="0")

    response = admin_client.post(reverse("admin:catalog_product_add"), data)

    assert response.status_code == 200
    assert not Product.objects.exists()


def test_la_accion_publicar_solo_publica_los_productos_completos(
    admin_client, complete_product, necklaces
):
    incomplete = Product.objects.create(name_es="A medias", category=necklaces, price_cents=1000)
    data = {
        "action": "publish",
        ACTION_CHECKBOX_NAME: [complete_product.pk, incomplete.pk],
    }

    response = admin_client.post(reverse("admin:catalog_product_changelist"), data, follow=True)

    complete_product.refresh_from_db()
    incomplete.refresh_from_db()
    assert complete_product.is_active
    assert not incomplete.is_active
    assert "«A medias» no se ha publicado" in response.content.decode()


def test_la_accion_ocultar(admin_client, complete_product):
    complete_product.is_active = True
    complete_product.save()
    data = {"action": "unpublish", ACTION_CHECKBOX_NAME: [complete_product.pk]}

    admin_client.post(reverse("admin:catalog_product_changelist"), data)

    complete_product.refresh_from_db()
    assert not complete_product.is_active
