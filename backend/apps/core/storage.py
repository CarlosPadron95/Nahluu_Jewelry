"""
Almacenamiento de las fotos en Cloudinary.

Django guarda los archivos subidos a través de un "storage". Por defecto
es el disco del servidor, pero en Render el disco se borra en cada
despliegue y las fotos se perderían. Por eso, en producción, las fotos
van a Cloudinary, que además las sirve muy rápido en todo el mundo (CDN).

En la base de datos guardamos el nombre:   products/3f2a9c....webp
y en Cloudinary la foto se llama:           <carpeta>/products/3f2a9c...
(Cloudinary guarda el formato aparte, por eso su nombre va sin extensión).
"""

from pathlib import PurePosixPath
from urllib.parse import urlparse

import cloudinary
import cloudinary.api
import cloudinary.uploader
import urllib3
from cloudinary.exceptions import NotFound
from cloudinary.utils import cloudinary_url
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

# Si Cloudinary no responde en este tiempo, damos error en vez de esperar para siempre
TIMEOUT_SECONDS = 60

# Así empiezan las direcciones de las fotos servidas por Cloudinary
CLOUDINARY_UPLOAD_PATH = "/image/upload/"


@deconstructible
class CloudinaryStorage(Storage):
    """Guarda, sirve y borra los archivos subidos en Cloudinary."""

    def __init__(self, cloudinary_url="", folder="nahluu-local"):
        # CLOUDINARY_URL tiene esta forma: cloudinary://API_KEY:API_SECRET@CLOUD_NAME
        parsed = urlparse(cloudinary_url)
        if parsed.scheme != "cloudinary" or not all(
            [parsed.hostname, parsed.username, parsed.password]
        ):
            raise ImproperlyConfigured(
                "CLOUDINARY_URL no es válida. Cópiala de Cloudinary: Settings → API Keys."
            )

        cloudinary.config(
            cloud_name=parsed.hostname,
            api_key=parsed.username,
            api_secret=parsed.password,
            secure=True,  # siempre https
        )
        # Carpeta de este entorno: así no se mezclan las fotos de prueba y las reales
        self.folder = folder.strip("/")

    @staticmethod
    def _clean_name(name):
        """
        En Windows, Django a veces separa las carpetas con "\\" (products\\abc.webp).
        Cloudinary y las direcciones web usan siempre "/", así que lo cambiamos.
        """
        return str(name).replace("\\", "/")

    def _public_id(self, name):
        """products/abc.webp -> nahluu/products/abc"""
        return f"{self.folder}/{PurePosixPath(self._clean_name(name)).with_suffix('')}"

    def _save(self, name, content):
        """Sube el archivo a Cloudinary y devuelve el nombre que se guarda en la base de datos."""
        name = self._clean_name(name)
        content.seek(0)
        public_id = self._public_id(name)
        cloudinary.uploader.upload(
            content,
            public_id=public_id,
            # Carpeta donde se verá la foto en la web de Cloudinary (Media Library)
            asset_folder=str(PurePosixPath(public_id).parent),
            resource_type="image",
            # Nunca pisamos una foto que ya existe
            overwrite=False,
            unique_filename=False,
            timeout=TIMEOUT_SECONDS,
        )
        return name

    def _open(self, name, mode="rb"):
        """Descarga la foto desde Cloudinary (casi nunca hace falta)."""
        response = urllib3.request("GET", self.url(name), timeout=TIMEOUT_SECONDS)
        if response.status != 200:
            raise FileNotFoundError(f"La foto {name} no está en Cloudinary.")
        return ContentFile(response.data, name=name)

    def url(self, name):
        """Dirección pública de la foto, por ejemplo https://res.cloudinary.com/..."""
        extension = PurePosixPath(self._clean_name(name)).suffix.lstrip(".")
        url, _options = cloudinary_url(
            self._public_id(name), format=extension, resource_type="image", secure=True
        )
        return url

    def delete(self, name):
        """Borra la foto de Cloudinary y de la caché de su CDN."""
        cloudinary.uploader.destroy(
            self._public_id(name),
            resource_type="image",
            invalidate=True,
            timeout=TIMEOUT_SECONDS,
        )

    def exists(self, name):
        """Django lo usa antes de guardar para no pisar archivos con el mismo nombre."""
        try:
            cloudinary.api.resource(
                self._public_id(name), resource_type="image", timeout=TIMEOUT_SECONDS
            )
        except NotFound:
            return False
        return True

    def size(self, name):
        """Peso de la foto en bytes."""
        resource = cloudinary.api.resource(
            self._public_id(name), resource_type="image", timeout=TIMEOUT_SECONDS
        )
        return resource["bytes"]


def resized_url(url: str, width: int, height: int) -> str:
    """
    Pide a Cloudinary una versión recortada y pequeña de la foto.

    Sirve para las miniaturas del panel: en vez de descargar la foto de
    2560 px, Cloudinary prepara al vuelo una de, por ejemplo, 128 × 128.
    Si la foto no está en Cloudinary (en local), devuelve la misma dirección.
    """
    if CLOUDINARY_UPLOAD_PATH not in url:
        return url
    options = f"c_fill,w_{width},h_{height},f_auto,q_auto"
    return url.replace(CLOUDINARY_UPLOAD_PATH, f"{CLOUDINARY_UPLOAD_PATH}{options}/", 1)
