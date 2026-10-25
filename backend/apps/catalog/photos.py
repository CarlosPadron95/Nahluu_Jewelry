"""
Todo lo relacionado con las fotos del catálogo.

1. Validadores: comprueban la foto ANTES de guardarla (formato, peso y tamaño).
2. optimize_photo(): prepara la foto para la web.
   - La gira según cómo se hizo con el móvil (dato EXIF "Orientation").
   - Le QUITA los metadatos EXIF: las fotos del móvil pueden llevar la
     ubicación GPS de donde se hicieron (por ejemplo, el taller o la casa).
   - La reduce a 2560 px como máximo y la guarda en WebP, que pesa poco.
"""

import uuid
from io import BytesIO
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.images import get_image_dimensions
from django.core.validators import FileExtensionValidator
from PIL import Image, ImageOps

# --- Límites de las fotos ---

# Formatos que se pueden subir
ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]
# Peso máximo del archivo (también es el límite del plan gratis de Cloudinary)
MAX_UPLOAD_MB = 10
# El lado más corto tiene que medir al menos esto, para que se vea nítida al ampliarla
MIN_SIDE_PX = 800
# Fotos gigantes gastan mucha memoria del servidor al procesarlas
MAX_MEGAPIXELS = 40
# Tamaño máximo con el que guardamos la foto (lado más largo)
MAX_SIDE_PX = 2560
# Calidad de WebP: 88 se ve igual que el original y pesa mucho menos
WEBP_QUALITY = 88


def is_new_upload(photo) -> bool:
    """
    True si la foto se acaba de subir y todavía no se ha guardado.

    Las fotos ya guardadas no se vuelven a comprobar ni a procesar:
    en producción estarán en Cloudinary y habría que descargarlas cada vez.
    Django marca las fotos nuevas con _committed = False.
    """
    return bool(photo) and not getattr(photo, "_committed", True)


# --- Validadores ---

validate_photo_extension = FileExtensionValidator(
    allowed_extensions=ALLOWED_EXTENSIONS,
    message="Formato no permitido. Sube la foto en JPG, PNG o WebP.",
)


def validate_photo_size(photo):
    """La foto no puede pesar más de MAX_UPLOAD_MB."""
    if is_new_upload(photo) and photo.size > MAX_UPLOAD_MB * 1024 * 1024:
        raise ValidationError(
            f"La foto pesa demasiado. El máximo son {MAX_UPLOAD_MB} MB.",
            code="photo_too_heavy",
        )


def validate_photo_dimensions(photo):
    """La foto tiene que ser una imagen de verdad, ni muy pequeña ni gigante."""
    if not is_new_upload(photo):
        return

    width, height = get_image_dimensions(photo)
    if not width or not height:
        raise ValidationError("El archivo no es una foto válida.", code="invalid_photo")

    if min(width, height) < MIN_SIDE_PX:
        raise ValidationError(
            f"La foto es demasiado pequeña ({width} × {height} px). "
            f"El lado más corto tiene que medir al menos {MIN_SIDE_PX} px.",
            code="photo_too_small",
        )

    if width * height > MAX_MEGAPIXELS * 1_000_000:
        raise ValidationError(
            f"La foto es demasiado grande ({width} × {height} px). "
            f"Redúcela a menos de {MAX_MEGAPIXELS} megapíxeles.",
            code="photo_too_big",
        )


# Lista para usar directamente en los campos de los modelos
PHOTO_VALIDATORS = [validate_photo_extension, validate_photo_size, validate_photo_dimensions]


# --- Procesado ---


def optimize_photo(photo) -> ContentFile:
    """Devuelve una copia de la foto girada, sin metadatos, reducida y en WebP."""
    photo.seek(0)
    with Image.open(photo) as original:
        # Pillow lee la foto "de lado" si el móvil la guardó girada:
        # exif_transpose la pone derecha
        image = ImageOps.exif_transpose(original)
        # Guardamos el perfil de color para que los dorados no cambien de tono
        color_profile = original.info.get("icc_profile")

    # Reducimos la foto si es más grande de lo necesario (mantiene la proporción)
    image.thumbnail((MAX_SIDE_PX, MAX_SIDE_PX), Image.Resampling.LANCZOS)

    # WebP trabaja en RGB, o en RGBA si la foto tiene fondo transparente
    mode = "RGBA" if image.has_transparency_data else "RGB"
    if image.mode != mode:
        image = image.convert(mode)

    # Al guardar NO pasamos el EXIF: así se pierden la ubicación GPS,
    # el modelo del móvil, la fecha, etc.
    buffer = BytesIO()
    save_options = {"format": "WEBP", "quality": WEBP_QUALITY}
    if color_profile:
        save_options["icc_profile"] = color_profile
    image.save(buffer, **save_options)

    original_name = Path(photo.name).stem or "foto"
    return ContentFile(buffer.getvalue(), name=f"{original_name}.webp")


def random_photo_name(folder: str, filename: str) -> str:
    """
    Ruta con un nombre aleatorio, por ejemplo: products/3f2a9c....webp

    Así dos fotos con el mismo nombre no chocan y no se publica
    el nombre original del archivo (que puede tener datos personales).
    """
    extension = Path(filename).suffix.lower()
    return f"{folder}/{uuid.uuid4().hex}{extension}"
