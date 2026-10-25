"""
Tests del almacenamiento en Cloudinary.

No se conectan a Cloudinary de verdad: usan el fixture fake_cloudinary
(está en backend/conftest.py).
"""

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile

from apps.core.storage import CloudinaryStorage, resized_url

# Dirección inventada: cuenta "nahluu-test" con claves falsas
FAKE_URL = "cloudinary://123456789012345:secreto-de-prueba@nahluu-test"


@pytest.fixture
def storage():
    return CloudinaryStorage(cloudinary_url=FAKE_URL, folder="tienda-test")


def test_una_cloudinary_url_mal_copiada_da_un_error_claro():
    with pytest.raises(ImproperlyConfigured):
        CloudinaryStorage(cloudinary_url="https://cloudinary.com/mi-cuenta")


def test_la_direccion_publica_de_la_foto(storage):
    url = storage.url("products/abc123.webp")

    assert url == (
        "https://res.cloudinary.com/nahluu-test/image/upload/v1/tienda-test/products/abc123.webp"
    )


def test_subir_una_foto(storage, fake_cloudinary):
    name = storage.save("products/abc123.webp", ContentFile(b"datos de la foto"))

    upload = fake_cloudinary["uploads"][0]
    assert name == "products/abc123.webp"
    assert upload["public_id"] == "tienda-test/products/abc123"
    assert upload["asset_folder"] == "tienda-test/products"
    assert upload["data"] == b"datos de la foto"
    # Nunca se pisa una foto que ya existe
    assert upload["overwrite"] is False


def test_si_el_nombre_ya_existe_django_elige_otro(storage, fake_cloudinary):
    fake_cloudinary["existing"].add("tienda-test/products/abc123")

    name = storage.save("products/abc123.webp", ContentFile(b"datos"))

    assert name != "products/abc123.webp"
    assert name.startswith("products/abc123_")


def test_en_windows_las_barras_de_carpeta_se_corrigen(storage, fake_cloudinary):
    # En Windows, Django puede pasar el nombre con "\\" en vez de "/"
    name = storage._save("products\\abc123.webp", ContentFile(b"datos"))

    assert name == "products/abc123.webp"
    assert fake_cloudinary["uploads"][0]["public_id"] == "tienda-test/products/abc123"
    assert storage.url("products\\abc123.webp") == storage.url("products/abc123.webp")


def test_borrar_una_foto(storage, fake_cloudinary):
    storage.delete("products/abc123.webp")

    delete = fake_cloudinary["deletes"][0]
    assert delete["public_id"] == "tienda-test/products/abc123"
    # También se borra de la caché de la CDN
    assert delete["invalidate"] is True


def test_comprobar_si_existe_y_su_peso(storage, fake_cloudinary):
    assert not storage.exists("products/abc123.webp")

    storage.save("products/abc123.webp", ContentFile(b"datos"))

    assert storage.exists("products/abc123.webp")
    assert storage.size("products/abc123.webp") == 1234


def test_miniatura_de_una_foto_de_cloudinary():
    url = "https://res.cloudinary.com/demo/image/upload/tienda/products/abc.webp"

    assert resized_url(url, 128, 128) == (
        "https://res.cloudinary.com/demo/image/upload/"
        "c_fill,w_128,h_128,f_auto,q_auto/tienda/products/abc.webp"
    )


def test_miniatura_de_una_foto_local_no_cambia():
    assert resized_url("/media/products/abc.webp", 128, 128) == "/media/products/abc.webp"
