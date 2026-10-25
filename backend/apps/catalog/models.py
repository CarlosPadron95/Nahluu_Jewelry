"""
Modelos del catálogo: categorías, colecciones, productos y sus fotos.

Ideas importantes:
- Los textos que ve el cliente van en dos idiomas: campo_es y campo_en.
- Los precios se guardan en céntimos (4550 = 45,50 €), ver apps/core/money.py.
- Un producto solo se ve en la tienda si está publicado (is_active).
  Mientras es un borrador se puede guardar a medias; para publicarlo
  hacen falta los textos en los dos idiomas y al menos una foto.
"""

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify

from apps.core.models import TimeStampedModel
from apps.core.money import format_euros

from .photos import PHOTO_VALIDATORS, is_new_upload, optimize_photo, random_photo_name

# Con estas unidades o menos, la tienda muestra «Últimas unidades»
LOW_STOCK_THRESHOLD = 3

# Campos de texto que tienen que estar rellenos para publicar un producto
REQUIRED_TO_PUBLISH = ["name_en", "description_es", "description_en"]


def product_photo_path(instance, filename):
    """Carpeta y nombre de las fotos de producto."""
    return random_photo_name("products", filename)


def collection_photo_path(instance, filename):
    """Carpeta y nombre de las fotos de colección."""
    return random_photo_name("collections", filename)


class Category(TimeStampedModel):
    """Tipo de joya: collares, pendientes..."""

    name_es = models.CharField("nombre (español)", max_length=60)
    name_en = models.CharField("nombre (inglés)", max_length=60)
    slug = models.SlugField(
        "dirección web",
        max_length=70,
        unique=True,
        help_text="Parte de la dirección de la página. Solo minúsculas, números y guiones.",
    )
    position = models.PositiveSmallIntegerField(
        "orden", default=0, help_text="Las de número más bajo salen primero."
    )

    class Meta:
        verbose_name = "categoría"
        verbose_name_plural = "categorías"
        ordering = ["position", "name_es"]

    def __str__(self):
        return self.name_es


class Collection(TimeStampedModel):
    """Grupo de piezas con una misma inspiración, por ejemplo «Océano»."""

    name_es = models.CharField("nombre (español)", max_length=80)
    name_en = models.CharField("nombre (inglés)", max_length=80)
    slug = models.SlugField(
        "dirección web",
        max_length=90,
        unique=True,
        help_text="Parte de la dirección de la página. Solo minúsculas, números y guiones.",
    )
    description_es = models.TextField("descripción (español)", blank=True)
    description_en = models.TextField("descripción (inglés)", blank=True)
    image = models.ImageField(
        "foto de portada",
        upload_to=collection_photo_path,
        validators=PHOTO_VALIDATORS,
        width_field="image_width",
        height_field="image_height",
        blank=True,
    )
    # Django rellena solo el ancho y el alto de la foto.
    # La web los necesita para reservar el hueco y que la página no "salte" al cargar.
    image_width = models.PositiveIntegerField(editable=False, null=True)
    image_height = models.PositiveIntegerField(editable=False, null=True)
    position = models.PositiveSmallIntegerField(
        "orden", default=0, help_text="Las de número más bajo salen primero."
    )
    is_active = models.BooleanField(
        "visible en la tienda",
        default=True,
        help_text="Desmárcalo para ocultar la colección sin borrarla.",
    )

    class Meta:
        verbose_name = "colección"
        verbose_name_plural = "colecciones"
        ordering = ["position", "name_es"]

    def __str__(self):
        return self.name_es

    def save(self, *args, **kwargs):
        # Si se acaba de subir una foto, la optimizamos antes de guardarla
        if is_new_upload(self.image):
            self.image = optimize_photo(self.image)
        super().save(*args, **kwargs)


class ProductQuerySet(models.QuerySet):
    """Consultas habituales de productos."""

    def published(self):
        """Solo los productos que se ven en la tienda."""
        return self.filter(is_active=True)

    def for_shop(self):
        """
        Productos publicados con todo lo que necesita la tienda.

        - select_related y prefetch_related traen la categoría, la colección
          y las fotos en muy pocas consultas (y no una por producto).
        - sold_out_rank vale 1 si está agotado: sirve para ordenar
          los agotados siempre al final.
        """
        return (
            self.published()
            .select_related("category", "collection")
            .prefetch_related("images")
            .annotate(
                sold_out_rank=models.Case(
                    models.When(stock=0, then=models.Value(1)),
                    default=models.Value(0),
                )
            )
        )


class Product(TimeStampedModel):
    """Una joya de la tienda. Talla única: no hay variantes."""

    # --- Textos ---
    name_es = models.CharField("nombre (español)", max_length=120)
    name_en = models.CharField("nombre (inglés)", max_length=120, blank=True)
    slug = models.SlugField(
        "dirección web",
        max_length=140,
        unique=True,
        help_text="Parte de la dirección de la página. Se rellena sola con el nombre.",
    )
    description_es = models.TextField("descripción (español)", blank=True)
    description_en = models.TextField("descripción (inglés)", blank=True)
    details_es = models.TextField(
        "detalles (español)",
        blank=True,
        help_text="Medidas, materiales, cierre... Escribe un detalle por línea.",
    )
    details_en = models.TextField("detalles (inglés)", blank=True)

    # --- Organización ---
    category = models.ForeignKey(
        Category,
        verbose_name="categoría",
        on_delete=models.PROTECT,  # no se puede borrar una categoría con productos
        related_name="products",
    )
    collection = models.ForeignKey(
        Collection,
        verbose_name="colección",
        on_delete=models.SET_NULL,  # si se borra la colección, el producto se queda sin ella
        related_name="products",
        null=True,
        blank=True,
    )
    position = models.PositiveIntegerField(
        "orden",
        default=0,
        help_text="Orden en «Destacados». Los de número más bajo salen primero.",
    )

    # --- Precio y stock ---
    price_cents = models.PositiveIntegerField(
        "precio (céntimos)", validators=[MinValueValidator(1)]
    )
    stock = models.PositiveIntegerField(
        "stock", default=0, help_text="Unidades que quedan para vender. Con 0 sale «Agotado»."
    )
    weight_grams = models.PositiveIntegerField(
        "peso (g)",
        null=True,
        blank=True,
        help_text="Peso de la joya. Sirve para calcular envíos y para la aduana.",
    )

    # --- Escaparate ---
    is_active = models.BooleanField(
        "publicado",
        default=False,
        help_text="Solo los productos publicados se ven en la tienda.",
    )
    is_new = models.BooleanField("etiqueta «Nuevo»", default=False)
    is_featured = models.BooleanField("destacado en la portada", default=False)

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = "producto"
        verbose_name_plural = "productos"
        ordering = ["position", "-created_at"]
        constraints = [
            # Segunda barrera en la propia base de datos: nunca un precio de 0 €
            models.CheckConstraint(
                condition=models.Q(price_cents__gt=0),
                name="catalog_product_price_positive",
            ),
        ]

    def __str__(self):
        return self.name_es

    def save(self, *args, **kwargs):
        # Si no hay dirección web, la creamos a partir del nombre
        if not self.slug:
            self.slug = slugify(self.name_es)
        super().save(*args, **kwargs)

    def clean(self):
        """Para publicar un producto, los textos tienen que estar completos."""
        super().clean()
        if not self.is_active:
            return
        errors = {
            field: "Obligatorio para publicar el producto."
            for field in REQUIRED_TO_PUBLISH
            if not getattr(self, field).strip()
        }
        if errors:
            raise ValidationError(errors)

    def publishing_problems(self) -> list[str]:
        """Lista de lo que falta para poder publicar el producto (vacía si está listo)."""
        problems = [
            f"falta «{self._meta.get_field(field).verbose_name}»"
            for field in REQUIRED_TO_PUBLISH
            if not getattr(self, field).strip()
        ]
        if not self.images.all():
            problems.append("falta al menos una foto")
        return problems

    @property
    def price_display(self) -> str:
        """Precio listo para mostrar: «45,50 €»."""
        return format_euros(self.price_cents)

    @property
    def is_sold_out(self) -> bool:
        """Etiqueta «Agotado»."""
        return self.stock == 0

    @property
    def is_low_stock(self) -> bool:
        """Etiqueta «Últimas unidades»."""
        return 0 < self.stock <= LOW_STOCK_THRESHOLD

    @property
    def labels(self) -> list[str]:
        """Etiquetas que verá el cliente en la tarjeta del producto."""
        labels = []
        if self.is_new:
            labels.append("Nuevo")
        if self.is_sold_out:
            labels.append("Agotado")
        elif self.is_low_stock:
            labels.append("Últimas unidades")
        return labels


class ProductImage(TimeStampedModel):
    """Una foto de un producto. La primera (orden más bajo) es la principal."""

    product = models.ForeignKey(
        Product,
        verbose_name="producto",
        on_delete=models.CASCADE,  # si se borra el producto, se borran sus fotos
        related_name="images",
    )
    image = models.ImageField(
        "foto",
        upload_to=product_photo_path,
        validators=PHOTO_VALIDATORS,
        width_field="width",
        height_field="height",
        help_text="JPG, PNG o WebP. Mínimo 800 px de lado, máximo 10 MB.",
    )
    width = models.PositiveIntegerField(editable=False, null=True)
    height = models.PositiveIntegerField(editable=False, null=True)
    alt_es = models.CharField(
        "descripción de la foto (español)",
        max_length=150,
        blank=True,
        help_text="Qué se ve en la foto. La usan los lectores de pantalla y Google. "
        "Si la dejas vacía se usa el nombre del producto.",
    )
    alt_en = models.CharField("descripción de la foto (inglés)", max_length=150, blank=True)
    position = models.PositiveSmallIntegerField("orden", default=0)

    class Meta:
        verbose_name = "foto"
        verbose_name_plural = "fotos"
        ordering = ["position", "id"]

    def __str__(self):
        return f"Foto de {self.product}"

    def save(self, *args, **kwargs):
        # Si se acaba de subir una foto, la optimizamos antes de guardarla
        if is_new_upload(self.image):
            self.image = optimize_photo(self.image)
        super().save(*args, **kwargs)
