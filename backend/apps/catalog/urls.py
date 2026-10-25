"""Rutas de la API del catálogo. Todas empiezan por /api/catalog/."""

from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("categories/", views.CategoryListView.as_view(), name="category-list"),
    path("collections/", views.CollectionListView.as_view(), name="collection-list"),
    path(
        "collections/<slug:slug>/",
        views.CollectionDetailView.as_view(),
        name="collection-detail",
    ),
    path("products/", views.ProductListView.as_view(), name="product-list"),
    path("products/<slug:slug>/", views.ProductDetailView.as_view(), name="product-detail"),
]
