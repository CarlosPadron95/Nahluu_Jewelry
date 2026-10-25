"""Tests de las utilidades de dinero."""

from decimal import Decimal

import pytest

from apps.core.money import cents_to_euros, euros_to_cents, format_euros


@pytest.mark.parametrize(
    ("euros", "cents"),
    [
        (Decimal("45"), 4500),
        (Decimal("45.5"), 4550),
        (Decimal("45.50"), 4550),
        (Decimal("0.01"), 1),
        (Decimal("1234.99"), 123499),
    ],
)
def test_euros_a_centimos(euros, cents):
    assert euros_to_cents(euros) == cents


def test_centimos_a_euros():
    assert cents_to_euros(4550) == Decimal("45.50")


@pytest.mark.parametrize(
    ("cents", "text"),
    [
        (4550, "45,50 €"),
        (4500, "45,00 €"),
        (99, "0,99 €"),
        (123499, "1.234,99 €"),
    ],
)
def test_formato_espanol(cents, text):
    # \u00a0 es el espacio "duro" que va antes del €
    assert format_euros(cents) == text.replace(" ", "\u00a0")
