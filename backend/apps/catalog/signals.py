"""
Borrado automático de los archivos de las fotos.

Django borra la fila de la base de datos, pero NO el archivo de la foto.
Sin esto, cada foto borrada o cambiada por otra se quedaría ocupando
espacio para siempre (y en Cloudinary el espacio cuenta).

Usamos transaction.on_commit: el archivo solo se borra cuando el cambio
se ha guardado de verdad en la base de datos. Si algo falla y se deshace,
la foto sigue en su sitio.
"""

from django.db import transaction
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from .models import Collection, ProductImage


def delete_file_after_commit(storage, name):
    """Borra el archivo del almacenamiento cuando termine la transacción."""
    if name:
        transaction.on_commit(lambda: storage.delete(name))


@receiver(post_delete, sender=ProductImage)
@receiver(post_delete, sender=Collection)
def delete_photo_of_deleted_object(sender, instance, **kwargs):
    """Al borrar una foto (o una colección), borramos también su archivo."""
    delete_file_after_commit(instance.image.storage, instance.image.name)


@receiver(pre_save, sender=ProductImage)
@receiver(pre_save, sender=Collection)
def delete_replaced_photo(sender, instance, **kwargs):
    """Si se cambia la foto por otra (o se quita), borramos el archivo viejo."""
    if not instance.pk:
        return  # es nuevo: no hay foto vieja

    old_name = sender.objects.filter(pk=instance.pk).values_list("image", flat=True).first()
    if old_name and old_name != instance.image.name:
        delete_file_after_commit(instance.image.storage, old_name)
