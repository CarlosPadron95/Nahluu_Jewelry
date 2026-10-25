"""
Idiomas de la API.

La web pide los textos en español o en inglés de dos formas:
1. Con ?lang=en en la dirección (manda sobre lo demás).
2. Con la cabecera Accept-Language, que Django lee en LocaleMiddleware.

Si el idioma no es uno de los nuestros, se usa el español.
"""

from django.conf import settings

# Idiomas de la tienda: {"es", "en"}
SUPPORTED_LANGUAGES = {code for code, _name in settings.LANGUAGES}


def get_request_language(request) -> str:
    """Idioma en el que hay que responder a esta petición."""
    language = request.GET.get("lang", "")
    if language in SUPPORTED_LANGUAGES:
        return language

    # El que ha elegido LocaleMiddleware a partir de Accept-Language
    language = getattr(request, "LANGUAGE_CODE", "")
    if language in SUPPORTED_LANGUAGES:
        return language

    return settings.LANGUAGE_CODE


def translated(obj, field: str, language: str) -> str:
    """
    Devuelve el texto en el idioma pedido: name_es o name_en, por ejemplo.

    Si el texto en inglés está vacío, devolvemos el español:
    mejor un texto en otro idioma que un hueco en la página.
    """
    value = getattr(obj, f"{field}_{language}", "")
    return value or getattr(obj, f"{field}_{settings.LANGUAGE_CODE}")


class LanguageContextMixin:
    """Para vistas de DRF: pasa el idioma de la petición a los serializers."""

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["language"] = get_request_language(self.request)
        return context
