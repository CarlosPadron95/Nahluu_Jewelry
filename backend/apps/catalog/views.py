"""
API pública del catálogo (solo lectura).

Todas las vistas son públicas (AllowAny) porque cualquier visitante puede
ver la tienda, pero solo aceptan GET: nadie puede cambiar nada desde aquí.
Los cambios se hacen siempre desde el panel de administración.
"""

from django.db.models import Count, Q
from rest_framework import generics
from rest_framework.permissions import AllowAny

from apps.core.i18n import LanguageContextMixin
from apps.core.pagination import StandardPagination

from .models import Category, Collection, Product
from .serializers import (
    CategorySerializer,
    CollectionSerializer,
    ProductCardSerializer,
    ProductDetailSerializer,
    ProductFilterSerializer,
)

# Cuenta solo los productos publicados (para «Collares (12)», por ejemplo)
published_products_count = Count("products", filter=Q(products__is_active=True))


class CategoryListView(LanguageContextMixin, generics.ListAPIView):
    """GET /api/catalog/categories/ → todas las categorías."""

    permission_classes = [AllowAny]
    serializer_class = CategorySerializer
    pagination_class = None  # son pocas: van todas juntas

    def get_queryset(self):
        # Con Count, Django ignora el orden de Meta: hay que repetirlo con order_by
        return Category.objects.annotate(product_count=published_products_count).order_by(
            "position", "name_es"
        )


class CollectionListView(LanguageContextMixin, generics.ListAPIView):
    """GET /api/catalog/collections/ → las colecciones visibles."""

    permission_classes = [AllowAny]
    serializer_class = CollectionSerializer
    pagination_class = None

    def get_queryset(self):
        return (
            Collection.objects.filter(is_active=True)
            .annotate(product_count=published_products_count)
            .order_by("position", "name_es")
        )


class CollectionDetailView(LanguageContextMixin, generics.RetrieveAPIView):
    """GET /api/catalog/collections/<slug>/ → una colección."""

    permission_classes = [AllowAny]
    serializer_class = CollectionSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return Collection.objects.filter(is_active=True).annotate(
            product_count=published_products_count
        )


class ProductListView(LanguageContextMixin, generics.ListAPIView):
    """
    GET /api/catalog/products/ → productos publicados, por páginas.

    Filtros opcionales (se pueden combinar):
        ?category=collares        solo una categoría
        ?collection=oceano        solo una colección
        ?featured=true            solo los destacados
        ?new=true                 solo los que llevan la etiqueta «Nuevo»
        ?q=corazon                buscador (sin importar acentos ni mayúsculas)
        ?ordering=price_asc       featured (por defecto), newest, price_asc, price_desc
        ?page=2&page_size=12      paginación
    """

    permission_classes = [AllowAny]
    serializer_class = ProductCardSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        # Primero comprobamos los filtros: si hay alguno mal, la API responde 400
        filters = ProductFilterSerializer(data=self.request.query_params)
        filters.is_valid(raise_exception=True)
        params = filters.validated_data

        products = Product.objects.for_shop()

        if params.get("category"):
            products = products.filter(category__slug=params["category"])
        if params.get("collection"):
            products = products.filter(collection__slug=params["collection"])
        if params.get("featured"):
            products = products.filter(is_featured=True)
        if params.get("new"):
            products = products.filter(is_new=True)

        search = params.get("q", "").strip()
        if search:
            # unaccent quita las tildes: «corazon» encuentra «Corazón»
            products = products.filter(
                Q(name_es__unaccent__icontains=search)
                | Q(name_en__unaccent__icontains=search)
                | Q(description_es__unaccent__icontains=search)
                | Q(description_en__unaccent__icontains=search)
            )

        return products.order_by(*ProductFilterSerializer.ORDERINGS[params["ordering"]])


class ProductDetailView(LanguageContextMixin, generics.RetrieveAPIView):
    """GET /api/catalog/products/<slug>/ → ficha completa de un producto publicado."""

    permission_classes = [AllowAny]
    serializer_class = ProductDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        # Los borradores no existen para la tienda: devuelven 404
        return Product.objects.for_shop()
