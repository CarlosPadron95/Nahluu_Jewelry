"""Formularios del panel de administración del catálogo."""

from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError

from apps.core.money import cents_to_euros, euros_to_cents

from .models import Product


class ProductAdminForm(forms.ModelForm):
    """
    Formulario del producto.

    En la base de datos el precio va en céntimos, pero en el panel
    se escribe en euros (45,50) porque es mucho más cómodo.
    """

    price = forms.DecimalField(
        label="Precio (€)",
        max_digits=8,
        decimal_places=2,
        min_value=Decimal("0.01"),
        # localize=True acepta la coma española: 45,50
        localize=True,
        help_text="Precio final que paga el cliente. Por ejemplo: 45 o 45,50",
    )

    class Meta:
        model = Product
        # Todos los campos menos price_cents, que se rellena con el precio en euros
        fields = [
            "name_es",
            "slug",
            "description_es",
            "details_es",
            "name_en",
            "description_en",
            "details_en",
            "category",
            "collection",
            "position",
            "stock",
            "weight_grams",
            "is_active",
            "is_new",
            "is_featured",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si editamos un producto que ya existe, mostramos su precio en euros
        if self.instance.pk:
            self.initial["price"] = cents_to_euros(self.instance.price_cents)

    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get("price")
        if price is not None:
            # Guardamos el precio en céntimos en el producto
            self.instance.price_cents = euros_to_cents(price)
        return cleaned_data


class ProductImageInlineFormSet(forms.BaseInlineFormSet):
    """Fotos del producto: un producto publicado necesita al menos una."""

    def clean(self):
        super().clean()
        if not self.instance.is_active:
            return

        # Contamos las fotos que quedarán al guardar (sin las marcadas para borrar)
        remaining_photos = sum(
            1
            for form in self.forms
            if form.cleaned_data
            and form.cleaned_data.get("image")
            and not form.cleaned_data.get("DELETE", False)
        )
        if remaining_photos == 0:
            raise ValidationError("Un producto publicado necesita al menos una foto.")
