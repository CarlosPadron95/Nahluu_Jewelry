"""
Serializers del catálogo: convierten los modelos en el JSON que lee la web.

Todos devuelven los textos en el idioma de la petición (ver apps/core/i18n.py).
Nunca enviamos el número exacto de unidades en stock: es un dato interno
de la tienda. La web solo necesita saber si está agotado o quedan pocas.
"""

from rest_framework import serializers

from apps.core.i18n import translated
from apps.core.money import CURRENCY

from .models import Category, Collection, Product

# Cuántos productos se muestran en «También te puede gustar»
RELATED_PRODUCTS_LIMIT = 4


def photo_data(photo, width, height, alt, request):
    """Datos de una foto: dirección completa, tamaño y texto alternativo."""
    if not photo:
        return None
    return {
        # build_absolute_uri convierte /media/... en http://servidor/media/...
        # (las direcciones de Cloudinary ya vienen completas y no cambian)
        "url": request.build_absolute_uri(photo.url),
        "width": width,
        "height": height,
        "alt": alt,
    }


class TranslatedMixin:
    """Ayuda para los serializers con textos en dos idiomas."""

    @property
    def language(self):
        return self.context.get("language", "es")

    def tr(self, obj, field):
        """Texto del campo en el idioma de la petición."""
        return translated(obj, field, self.language)


class CategorySerializer(TranslatedMixin, serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    product_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ["slug", "name", "product_count"]

    def get_name(self, category):
        return self.tr(category, "name")


class CollectionSerializer(TranslatedMixin, serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    product_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Collection
        fields = ["slug", "name", "description", "image", "product_count"]

    def get_name(self, collection):
        return self.tr(collection, "name")

    def get_description(self, collection):
        return self.tr(collection, "description")

    def get_image(self, collection):
        return photo_data(
            collection.image,
            collection.image_width,
            collection.image_height,
            alt=self.tr(collection, "name"),
            request=self.context["request"],
        )


class ProductCardSerializer(TranslatedMixin, serializers.ModelSerializer):
    """Lo que necesita la tarjeta de un producto en las listas."""

    name = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    collection = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    hover_image = serializers.SerializerMethodField()
    is_low_stock = serializers.BooleanField(read_only=True)
    is_sold_out = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "slug",
            "name",
            "price_cents",
            "currency",
            "category",
            "collection",
            "image",
            "hover_image",
            "is_new",
            "is_low_stock",
            "is_sold_out",
        ]

    def get_name(self, product):
        return self.tr(product, "name")

    def get_currency(self, product):
        return CURRENCY

    def get_category(self, product):
        return {"slug": product.category.slug, "name": self.tr(product.category, "name")}

    def get_collection(self, product):
        if product.collection is None:
            return None
        return {"slug": product.collection.slug, "name": self.tr(product.collection, "name")}

    def photos(self, product):
        """Fotos del producto en orden. Usa las que ya trajo prefetch_related."""
        return list(product.images.all())

    def serialize_photo(self, product, photo):
        # Si la foto no tiene descripción, usamos el nombre del producto
        alt = self.tr(photo, "alt") or self.tr(product, "name")
        return photo_data(photo.image, photo.width, photo.height, alt, self.context["request"])

    def get_image(self, product):
        """Foto principal."""
        photos = self.photos(product)
        return self.serialize_photo(product, photos[0]) if photos else None

    def get_hover_image(self, product):
        """Segunda foto: en escritorio se muestra al pasar el ratón por la tarjeta."""
        photos = self.photos(product)
        return self.serialize_photo(product, photos[1]) if len(photos) > 1 else None


class ProductDetailSerializer(ProductCardSerializer):
    """Ficha completa de un producto."""

    description = serializers.SerializerMethodField()
    details = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    related = serializers.SerializerMethodField()

    class Meta(ProductCardSerializer.Meta):
        fields = [
            *ProductCardSerializer.Meta.fields,
            "description",
            "details",
            "images",
            "related",
        ]

    def get_description(self, product):
        return self.tr(product, "description")

    def get_details(self, product):
        """Los detalles se escriben uno por línea; aquí los separamos en una lista."""
        text = self.tr(product, "details")
        return [line.strip() for line in text.splitlines() if line.strip()]

    def get_images(self, product):
        """Todas las fotos, para la galería ampliable."""
        return [self.serialize_photo(product, photo) for photo in self.photos(product)]

    def get_related(self, product):
        """
        «También te puede gustar»: primero piezas de la misma colección
        y, si no llegan a 4, se completa con piezas de la misma categoría.
        """
        others = Product.objects.for_shop().exclude(pk=product.pk)
        ordering = ["sold_out_rank", "position", "-created_at", "-id"]

        related = []
        if product.collection_id:
            related = list(
                others.filter(collection_id=product.collection_id).order_by(*ordering)[
                    :RELATED_PRODUCTS_LIMIT
                ]
            )

        missing = RELATED_PRODUCTS_LIMIT - len(related)
        if missing > 0:
            already_chosen = [item.pk for item in related]
            related += list(
                others.filter(category_id=product.category_id)
                .exclude(pk__in=already_chosen)
                .order_by(*ordering)[:missing]
            )

        return ProductCardSerializer(related, many=True, context=self.context).data


class ProductFilterSerializer(serializers.Serializer):
    """
    Comprueba los filtros de la lista de productos (lo que va después del ? en la dirección).

    Si alguien manda un valor raro (por ejemplo ?ordering=hackeo),
    la API responde con un error 400 claro en vez de fallar.
    """

    # Ordenaciones disponibles y cómo se traducen a la base de datos.
    # Los agotados siempre van al final, y "-id" deja el orden fijo entre páginas.
    ORDERINGS = {
        "featured": ["sold_out_rank", "position", "-created_at", "-id"],
        "newest": ["sold_out_rank", "-created_at", "-id"],
        "price_asc": ["sold_out_rank", "price_cents", "-created_at", "-id"],
        "price_desc": ["sold_out_rank", "-price_cents", "-created_at", "-id"],
    }

    category = serializers.SlugField(required=False)
    collection = serializers.SlugField(required=False)
    featured = serializers.BooleanField(required=False)
    new = serializers.BooleanField(required=False)
    q = serializers.CharField(required=False, allow_blank=True, max_length=100)
    ordering = serializers.ChoiceField(choices=list(ORDERINGS), default="featured")
