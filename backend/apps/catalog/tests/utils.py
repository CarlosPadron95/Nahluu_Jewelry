"""Ayudas para los tests del catálogo."""

from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image


def make_photo_file(name="foto.jpg", size=(1200, 900), image_format="JPEG", exif=None):
    """
    Crea una foto de prueba en memoria, como si la subiera alguien desde el panel.

    exif: datos EXIF opcionales (por ejemplo, una ubicación GPS de mentira).
    """
    if image_format == "PNG":
        # PNG con fondo semitransparente (el último número es la transparencia)
        image = Image.new("RGBA", size, color=(133, 102, 62, 128))
    else:
        image = Image.new("RGB", size, color=(133, 102, 62))  # dorado de la marca
    buffer = BytesIO()
    save_options = {"format": image_format}
    if exif is not None:
        save_options["exif"] = exif
    image.save(buffer, **save_options)
    content_type = f"image/{image_format.lower()}"
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=content_type)


def make_published_product(category, name_es, photos=1, **fields):
    """
    Crea un producto publicado y completo, con sus fotos.

    fields: cualquier otro campo que queramos cambiar (price_cents, stock...).
    """
    from apps.catalog.models import Product, ProductImage

    data = {
        "name_en": f"{name_es} (EN)",
        "description_es": f"Descripción de {name_es}.",
        "description_en": f"Description of {name_es}.",
        "price_cents": 3000,
        "stock": 5,
        "is_active": True,
        **fields,
    }
    product = Product.objects.create(name_es=name_es, category=category, **data)
    for position in range(photos):
        ProductImage.objects.create(product=product, image=make_photo_file(), position=position)
    return product
