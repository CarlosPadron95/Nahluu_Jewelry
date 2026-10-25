"""
Test de principio a fin: una foto de producto guardada en Cloudinary.

Usa el fixture cloudinary_storage_settings (backend/conftest.py), así que
no se conecta a Cloudinary de verdad.
"""

from apps.catalog.models import ProductImage

from .utils import make_photo_file


def test_la_foto_del_producto_se_sube_y_se_borra_de_cloudinary(
    draft_product, cloudinary_storage_settings, django_capture_on_commit_callbacks
):
    fake_cloudinary = cloudinary_storage_settings

    photo = ProductImage.objects.create(product=draft_product, image=make_photo_file())

    # Se ha subido ya optimizada (WebP) y con la dirección de Cloudinary
    upload = fake_cloudinary["uploads"][0]
    assert upload["public_id"].startswith("tienda-test/products/")
    assert upload["data"][8:12] == b"WEBP"  # así empiezan por dentro los archivos WebP
    assert photo.image.url.startswith("https://res.cloudinary.com/nahluu-test/image/upload/")
    assert photo.image.url.endswith(".webp")

    # Al borrar la foto, también se borra de Cloudinary
    with django_capture_on_commit_callbacks(execute=True):
        photo.delete()

    assert fake_cloudinary["deletes"][0]["public_id"] == upload["public_id"]


def test_las_miniaturas_del_panel_piden_una_foto_pequena(
    cloudinary_storage_settings, admin_client, complete_product
):
    # complete_product ya trae una foto, que se ha subido a Cloudinary (falso)
    response = admin_client.get("/admin/catalog/product/")

    assert "/image/upload/c_fill,w_128,h_128,f_auto,q_auto/" in response.content.decode()
