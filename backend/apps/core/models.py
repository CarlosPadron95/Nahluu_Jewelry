"""Modelos base que reutilizan las demás aplicaciones."""

from django.db import models


class TimeStampedModel(models.Model):
    """
    Añade a cualquier modelo la fecha de creación y la de la última modificación.

    Es "abstracto": no crea una tabla propia, solo presta sus campos
    a los modelos que heredan de él.
    """

    created_at = models.DateTimeField("creado", auto_now_add=True)
    updated_at = models.DateTimeField("modificado", auto_now=True)

    class Meta:
        abstract = True
