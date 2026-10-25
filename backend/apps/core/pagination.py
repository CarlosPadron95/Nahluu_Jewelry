"""Paginación de la API: las listas largas se envían por páginas."""

from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """
    Páginas de 24 elementos (cuadra con rejillas de 2, 3 y 4 columnas).

    La web puede pedir otro tamaño con ?page_size=12, pero nunca más de 48,
    para que nadie pueda pedir todo el catálogo de golpe.
    """

    page_size = 24
    page_size_query_param = "page_size"
    max_page_size = 48
