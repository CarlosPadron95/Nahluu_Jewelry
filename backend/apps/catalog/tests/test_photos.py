"""Tests de las fotos: validación, optimización y borrado de archivos."""

import pytest
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from PIL import Image

from apps.catalog.models import ProductImage
from apps.catalog.photos import MAX_SIDE_PX

from .utils import make_photo_file

# Etiquetas EXIF que usamos en los tests
ORIENTATION = 0x0112  # cómo estaba girado el móvil
CAMERA_MAKE = 0x010F  # marca del móvil
GPS_INFO = 0x8825  # ubicación GPS


def fake_phone_exif():
    """EXIF como el de una foto de móvil: girada 90° y con ubicación GPS."""
    exif = Image.Exif()
    exif[ORIENTATION] = 6  # 6 = el móvil estaba en vertical
    exif[CAMERA_MAKE] = "Apple"
    exif[GPS_INFO] = {1: "N", 2: (28.0, 6.0, 0.0), 3: "W", 4: (15.0, 25.0, 0.0)}
    return exif


def save_photo(product, photo_file):
    """Guarda una foto pasando antes por las validaciones, como hace el panel."""
    photo = ProductImage(product=product, image=photo_file)
    photo.full_clean()
    photo.save()
    return photo


# --- Optimización ---


def test_la_foto_se_guarda_en_webp_con_nombre_aleatorio(draft_product):
    photo = save_photo(draft_product, make_photo_file(name="IMG_1234 casa de Andrea.jpg"))

    assert photo.image.name.startswith("products/")
    assert photo.image.name.endswith(".webp")
    # El nombre original del archivo no se publica
    assert "IMG_1234" not in photo.image.name
    with default_storage.open(photo.image.name) as stored:
        assert Image.open(stored).format == "WEBP"


def test_se_borra_la_ubicacion_gps_y_los_datos_del_movil(draft_product):
    photo = save_photo(draft_product, make_photo_file(exif=fake_phone_exif()))

    with default_storage.open(photo.image.name) as stored:
        exif = Image.open(stored).getexif()

    assert len(exif) == 0
    assert GPS_INFO not in exif


def test_la_foto_se_gira_segun_el_movil(draft_product):
    # La foto llega "tumbada" (1200 × 900) con la marca de que el móvil estaba en vertical
    photo = save_photo(draft_product, make_photo_file(size=(1200, 900), exif=fake_phone_exif()))

    # Se guarda derecha: en vertical
    assert (photo.width, photo.height) == (900, 1200)


def test_las_fotos_grandes_se_reducen(draft_product):
    photo = save_photo(draft_product, make_photo_file(size=(4000, 3000)))

    assert max(photo.width, photo.height) == MAX_SIDE_PX
    assert (photo.width, photo.height) == (2560, 1920)


def test_las_fotos_png_con_transparencia_la_conservan(draft_product):
    photo = save_photo(draft_product, make_photo_file(name="pieza.png", image_format="PNG"))

    with default_storage.open(photo.image.name) as stored:
        assert Image.open(stored).mode == "RGBA"


# --- Validaciones ---


def test_no_se_aceptan_fotos_pequenas(draft_product):
    with pytest.raises(ValidationError) as error:
        save_photo(draft_product, make_photo_file(size=(600, 400)))

    assert error.value.error_dict["image"][0].code == "photo_too_small"


def test_no_se_aceptan_fotos_gigantes(draft_product, monkeypatch):
    # En vez de crear una foto enorme (gasta mucha memoria), bajamos el límite a 1 megapíxel
    monkeypatch.setattr("apps.catalog.photos.MAX_MEGAPIXELS", 1)

    with pytest.raises(ValidationError) as error:
        save_photo(draft_product, make_photo_file(size=(1200, 900)))

    assert error.value.error_dict["image"][0].code == "photo_too_big"


def test_no_se_aceptan_otros_formatos(draft_product):
    with pytest.raises(ValidationError) as error:
        save_photo(draft_product, make_photo_file(name="foto.gif", image_format="GIF"))

    assert "image" in error.value.message_dict


def test_no_se_aceptan_archivos_que_no_son_fotos(draft_product):
    from django.core.files.uploadedfile import SimpleUploadedFile

    fake = SimpleUploadedFile("foto.jpg", b"esto no es una foto", content_type="image/jpeg")

    with pytest.raises(ValidationError) as error:
        save_photo(draft_product, fake)

    assert error.value.error_dict["image"][0].code == "invalid_photo"


def test_no_se_aceptan_fotos_de_mas_de_10_mb(draft_product, monkeypatch):
    # En vez de crear un archivo enorme, bajamos el límite para el test
    monkeypatch.setattr("apps.catalog.photos.MAX_UPLOAD_MB", 0)

    with pytest.raises(ValidationError) as error:
        save_photo(draft_product, make_photo_file())

    assert error.value.error_dict["image"][0].code == "photo_too_heavy"


# --- Borrado de archivos ---


def test_al_borrar_la_foto_se_borra_el_archivo(draft_product, django_capture_on_commit_callbacks):
    photo = save_photo(draft_product, make_photo_file())
    file_name = photo.image.name

    # execute=True ejecuta lo que espera al final de la transacción (on_commit)
    with django_capture_on_commit_callbacks(execute=True):
        photo.delete()

    assert not default_storage.exists(file_name)


def test_al_borrar_el_producto_se_borran_sus_fotos(
    draft_product, django_capture_on_commit_callbacks
):
    photo = save_photo(draft_product, make_photo_file())
    file_name = photo.image.name

    with django_capture_on_commit_callbacks(execute=True):
        draft_product.delete()

    assert not default_storage.exists(file_name)


def test_al_cambiar_la_foto_se_borra_la_vieja(draft_product, django_capture_on_commit_callbacks):
    photo = save_photo(draft_product, make_photo_file())
    old_name = photo.image.name

    with django_capture_on_commit_callbacks(execute=True):
        photo.image = make_photo_file(name="nueva.jpg")
        photo.save()

    assert not default_storage.exists(old_name)
    assert default_storage.exists(photo.image.name)


def test_guardar_sin_cambiar_la_foto_no_la_borra(draft_product, django_capture_on_commit_callbacks):
    photo = save_photo(draft_product, make_photo_file())

    with django_capture_on_commit_callbacks(execute=True):
        photo.alt_es = "Collar sobre arena"
        photo.save()

    assert default_storage.exists(photo.image.name)
