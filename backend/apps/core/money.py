"""
Utilidades para trabajar con dinero.

En la base de datos guardamos siempre CÉNTIMOS en un número entero
(4550 = 45,50 €). Así no hay errores de redondeo como con los decimales
de coma flotante, y además Stripe también trabaja en céntimos.
"""

from decimal import ROUND_HALF_UP, Decimal

# La tienda cobra solo en euros (código ISO 4217, el que usa Stripe en minúsculas)
CURRENCY = "EUR"


def euros_to_cents(amount: Decimal) -> int:
    """Pasa de euros a céntimos: Decimal("45.5") -> 4550."""
    return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def cents_to_euros(cents: int) -> Decimal:
    """Pasa de céntimos a euros: 4550 -> Decimal("45.50")."""
    return (Decimal(cents) / 100).quantize(Decimal("0.01"))


def format_euros(cents: int) -> str:
    """Muestra un precio en formato español: 4550 -> "45,50 €"."""
    # Python escribe 1,234.50 (formato inglés)...
    text = f"{cents_to_euros(cents):,.2f}"
    # ...y lo pasamos a 1.234,50 cambiando los separadores
    text = text.replace(",", " ").replace(".", ",").replace(" ", ".")
    # Espacio "duro" (no separable) antes del €: así nunca se queda solo en otra línea
    return f"{text}\u00a0€"
