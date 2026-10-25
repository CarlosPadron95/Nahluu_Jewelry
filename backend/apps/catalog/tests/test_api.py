"""
Tests de la API pública del catálogo.

client es un navegador de pruebas SIN iniciar sesión: como cualquier visitante.
"""

import pytest
from django.urls import reverse

from apps.catalog.models import Category, Collection, Product, ProductImage

from .utils import make_photo_file, make_published_product

PRODUCTS_URL = reverse("catalog:product-list")


def product_url(slug):
    return reverse("catalog:product-detail", args=[slug])


def slugs(response):
    """Las direcciones web de los productos de una respuesta, en orden."""
    return [product["slug"] for product in response.json()["results"]]


@pytest.fixture
def earrings(db):
    return Category.objects.get(slug="pendientes")


@pytest.fixture
def ocean(db):
    return Collection.objects.create(name_es="Océano", name_en="Ocean", slug="oceano")


# --- Lista de productos ---


def test_la_lista_solo_muestra_productos_publicados(client, necklaces, draft_product):
    make_published_product(necklaces, "Collar Marea Alta")

    response = client.get(PRODUCTS_URL)

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert slugs(response) == ["collar-marea-alta"]


def test_la_tarjeta_trae_lo_que_necesita_la_web(client, necklaces, ocean):
    make_published_product(
        necklaces, "Collar Ola", photos=2, collection=ocean, is_new=True, stock=2
    )

    card = client.get(PRODUCTS_URL).json()["results"][0]

    assert card["name"] == "Collar Ola"
    assert card["price_cents"] == 3000
    assert card["currency"] == "EUR"
    assert card["category"] == {"slug": "collares", "name": "Collares"}
    assert card["collection"] == {"slug": "oceano", "name": "Océano"}
    assert card["is_new"] is True
    assert card["is_low_stock"] is True
    assert card["is_sold_out"] is False
    # Foto principal con su tamaño (para que la página no "salte" al cargar)
    assert card["image"]["url"].startswith("http://testserver/media/products/")
    assert card["image"]["width"] == 1200
    assert card["image"]["height"] == 900
    # Sin descripción, el texto alternativo es el nombre del producto
    assert card["image"]["alt"] == "Collar Ola"
    # Segunda foto, para cuando se pasa el ratón por encima
    assert card["hover_image"] is not None


def test_nunca_se_envia_el_stock_exacto(client, necklaces):
    make_published_product(necklaces, "Collar Secreto", stock=37)

    card = client.get(PRODUCTS_URL).json()["results"][0]

    assert "stock" not in card
    assert 37 not in card.values()


def test_textos_en_ingles_con_la_cabecera_del_navegador(client, necklaces, ocean):
    make_published_product(necklaces, "Collar Ola", collection=ocean)

    response = client.get(PRODUCTS_URL, headers={"accept-language": "en"})
    card = response.json()["results"][0]

    assert card["name"] == "Collar Ola (EN)"
    assert card["category"]["name"] == "Necklaces"
    assert card["collection"]["name"] == "Ocean"
    # Django avisa a las cachés de que la respuesta depende del idioma
    assert "Accept-Language" in response["Vary"]


def test_el_idioma_de_la_direccion_manda_sobre_el_del_navegador(client, necklaces):
    make_published_product(necklaces, "Collar Ola")

    response = client.get(PRODUCTS_URL, {"lang": "en"}, headers={"accept-language": "es"})

    assert response.json()["results"][0]["name"] == "Collar Ola (EN)"


def test_un_idioma_que_no_tenemos_responde_en_espanol(client, necklaces):
    make_published_product(necklaces, "Collar Ola")

    response = client.get(PRODUCTS_URL, {"lang": "fr"})

    assert response.json()["results"][0]["name"] == "Collar Ola"


def test_la_descripcion_de_la_foto_en_cada_idioma(client, draft_product):
    ProductImage.objects.create(
        product=draft_product,
        image=make_photo_file(),
        alt_es="Collar sobre arena",
        alt_en="Necklace on the sand",
    )
    Product.objects.filter(pk=draft_product.pk).update(is_active=True)

    card_es = client.get(PRODUCTS_URL).json()["results"][0]
    card_en = client.get(PRODUCTS_URL, {"lang": "en"}).json()["results"][0]

    assert card_es["image"]["alt"] == "Collar sobre arena"
    assert card_en["image"]["alt"] == "Necklace on the sand"


# --- Filtros, búsqueda y orden ---


def test_filtrar_por_categoria_y_coleccion(client, necklaces, earrings, ocean):
    make_published_product(necklaces, "Collar Ola", collection=ocean)
    make_published_product(necklaces, "Collar Roca")
    make_published_product(earrings, "Pendientes Ola", collection=ocean)

    by_category = client.get(PRODUCTS_URL, {"category": "pendientes"})
    by_collection = client.get(PRODUCTS_URL, {"collection": "oceano"})
    both = client.get(PRODUCTS_URL, {"category": "collares", "collection": "oceano"})

    assert slugs(by_category) == ["pendientes-ola"]
    assert set(slugs(by_collection)) == {"collar-ola", "pendientes-ola"}
    assert slugs(both) == ["collar-ola"]


def test_filtrar_destacados_y_nuevos(client, necklaces):
    make_published_product(necklaces, "Collar Destacado", is_featured=True)
    make_published_product(necklaces, "Collar Nuevo", is_new=True)
    make_published_product(necklaces, "Collar Normal")

    assert slugs(client.get(PRODUCTS_URL, {"featured": "true"})) == ["collar-destacado"]
    assert slugs(client.get(PRODUCTS_URL, {"new": "true"})) == ["collar-nuevo"]


def test_el_buscador_no_distingue_tildes_ni_mayusculas(client, necklaces):
    make_published_product(necklaces, "Collar Corazón")
    make_published_product(necklaces, "Collar Estrella")

    response = client.get(PRODUCTS_URL, {"q": "CORAZON"})

    assert slugs(response) == ["collar-corazon"]


def test_el_buscador_tambien_busca_en_ingles(client, necklaces):
    make_published_product(necklaces, "Collar Estrella", name_en="Star Necklace")

    response = client.get(PRODUCTS_URL, {"q": "star"})

    assert slugs(response) == ["collar-estrella"]


def test_ordenar_por_precio(client, necklaces):
    make_published_product(necklaces, "Collar Medio", price_cents=4000)
    make_published_product(necklaces, "Collar Barato", price_cents=2000)
    make_published_product(necklaces, "Collar Caro", price_cents=9000)

    cheap_first = client.get(PRODUCTS_URL, {"ordering": "price_asc"})
    expensive_first = client.get(PRODUCTS_URL, {"ordering": "price_desc"})

    assert slugs(cheap_first) == ["collar-barato", "collar-medio", "collar-caro"]
    assert slugs(expensive_first) == ["collar-caro", "collar-medio", "collar-barato"]


def test_ordenar_por_novedades(client, necklaces):
    make_published_product(necklaces, "Collar Antiguo")
    make_published_product(necklaces, "Collar Reciente")

    response = client.get(PRODUCTS_URL, {"ordering": "newest"})

    assert slugs(response) == ["collar-reciente", "collar-antiguo"]


def test_los_destacados_siguen_el_orden_del_panel(client, necklaces):
    make_published_product(necklaces, "Collar Segundo", position=2)
    make_published_product(necklaces, "Collar Primero", position=1)

    assert slugs(client.get(PRODUCTS_URL)) == ["collar-primero", "collar-segundo"]


def test_los_agotados_siempre_van_al_final(client, necklaces):
    make_published_product(necklaces, "Collar Agotado", price_cents=1000, stock=0)
    make_published_product(necklaces, "Collar Disponible", price_cents=5000)

    response = client.get(PRODUCTS_URL, {"ordering": "price_asc"})

    assert slugs(response) == ["collar-disponible", "collar-agotado"]


def test_una_ordenacion_que_no_existe_da_un_error_claro(client):
    response = client.get(PRODUCTS_URL, {"ordering": "hackeo"})

    assert response.status_code == 400
    assert "ordering" in response.json()


def test_la_lista_va_por_paginas(client, necklaces):
    for number in range(5):
        make_published_product(necklaces, f"Collar {number}", photos=0)

    response = client.get(PRODUCTS_URL, {"page_size": 2, "page": 2})
    data = response.json()

    assert data["count"] == 5
    assert len(data["results"]) == 2
    assert data["next"] is not None
    assert data["previous"] is not None


def test_no_se_pueden_pedir_paginas_gigantes(client, necklaces):
    for number in range(50):
        make_published_product(necklaces, f"Collar {number}", photos=0)

    response = client.get(PRODUCTS_URL, {"page_size": 1000})

    assert len(response.json()["results"]) == 48


def test_la_lista_hace_pocas_consultas_aunque_haya_muchos_productos(
    client, necklaces, ocean, django_assert_max_num_queries
):
    # Sin select_related/prefetch_related serían decenas de consultas (una por producto)
    for number in range(10):
        make_published_product(necklaces, f"Collar {number}", photos=2, collection=ocean)

    with django_assert_max_num_queries(3):
        response = client.get(PRODUCTS_URL)

    assert response.json()["count"] == 10


# --- Ficha de producto ---


def test_ficha_de_un_producto(client, necklaces):
    make_published_product(
        necklaces,
        "Collar Marea",
        photos=3,
        details_es="Plata 925 bañada en oro\n\nLargo: 45 cm\n",
        details_en="925 silver plated in gold\nLength: 45 cm",
    )

    data_es = client.get(product_url("collar-marea")).json()
    data_en = client.get(product_url("collar-marea"), {"lang": "en"}).json()

    assert data_es["description"] == "Descripción de Collar Marea."
    # Los detalles llegan como lista, sin líneas vacías
    assert data_es["details"] == ["Plata 925 bañada en oro", "Largo: 45 cm"]
    assert data_en["details"] == ["925 silver plated in gold", "Length: 45 cm"]
    assert len(data_es["images"]) == 3


def test_un_borrador_no_existe_para_la_tienda(client, draft_product):
    response = client.get(product_url(draft_product.slug))

    assert response.status_code == 404


def test_tambien_te_puede_gustar(client, necklaces, earrings, ocean):
    make_published_product(necklaces, "Collar Ola", collection=ocean)
    make_published_product(earrings, "Pendientes Ola", collection=ocean)
    make_published_product(necklaces, "Collar Roca")
    make_published_product(earrings, "Pendientes Roca")
    make_published_product(necklaces, "Collar Oculto", is_active=False)

    related = client.get(product_url("collar-ola")).json()["related"]
    related_slugs = [product["slug"] for product in related]

    # Primero la misma colección y después la misma categoría
    assert related_slugs == ["pendientes-ola", "collar-roca"]


def test_la_api_es_de_solo_lectura(client, necklaces):
    make_published_product(necklaces, "Collar Marea")

    assert client.post(PRODUCTS_URL, {}).status_code == 405
    assert client.delete(product_url("collar-marea")).status_code == 405


# --- Categorías y colecciones ---


def test_categorias_con_su_numero_de_productos_publicados(client, necklaces, draft_product):
    make_published_product(necklaces, "Collar Marea Alta")

    response = client.get(reverse("catalog:category-list"), {"lang": "en"})

    assert response.json() == [
        {"slug": "collares", "name": "Necklaces", "product_count": 1},
        {"slug": "pendientes", "name": "Earrings", "product_count": 0},
    ]


def test_solo_se_ven_las_colecciones_visibles(client, ocean):
    Collection.objects.create(name_es="Oculta", name_en="Hidden", slug="oculta", is_active=False)

    response = client.get(reverse("catalog:collection-list"))
    hidden = client.get(reverse("catalog:collection-detail", args=["oculta"]))

    assert [collection["slug"] for collection in response.json()] == ["oceano"]
    assert hidden.status_code == 404


def test_ficha_de_una_coleccion(client, ocean, necklaces):
    ocean.description_es = "Piezas inspiradas en el mar."
    ocean.image = make_photo_file()
    ocean.save()
    make_published_product(necklaces, "Collar Ola", collection=ocean)

    data = client.get(reverse("catalog:collection-detail", args=["oceano"])).json()

    assert data["name"] == "Océano"
    assert data["description"] == "Piezas inspiradas en el mar."
    assert data["product_count"] == 1
    assert data["image"]["url"].startswith("http://testserver/media/collections/")
