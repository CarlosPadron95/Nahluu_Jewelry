"""
Fixtures de pytest que comparten todas las aplicaciones.

Fakes de Cloudinary: los tests NUNCA se conectan a Cloudinary de verdad.
Cambiamos sus funciones por otras "de mentira" que apuntan lo que reciben.
Así los tests son rápidos, no gastan créditos y no necesitan claves.
"""

import cloudinary.api
import cloudinary.uploader
import pytest
from cloudinary.exceptions import NotFound

# Dirección de Cloudinary inventada para los tests
FAKE_CLOUDINARY_URL = "cloudinary://123456789012345:secreto-de-prueba@nahluu-test"


@pytest.fixture
def fake_cloudinary(monkeypatch):
    """Cambia las llamadas a Cloudinary por fakes y devuelve lo que han recibido."""
    calls = {"uploads": [], "deletes": [], "existing": set()}

    def fake_upload(file, **options):
        calls["uploads"].append({"data": file.read(), **options})
        calls["existing"].add(options["public_id"])
        return {"public_id": options["public_id"]}

    def fake_destroy(public_id, **options):
        calls["deletes"].append({"public_id": public_id, **options})
        calls["existing"].discard(public_id)
        return {"result": "ok"}

    def fake_resource(public_id, **options):
        if public_id not in calls["existing"]:
            raise NotFound("No existe")
        return {"public_id": public_id, "bytes": 1234}

    monkeypatch.setattr(cloudinary.uploader, "upload", fake_upload)
    monkeypatch.setattr(cloudinary.uploader, "destroy", fake_destroy)
    monkeypatch.setattr(cloudinary.api, "resource", fake_resource)
    return calls


@pytest.fixture
def cloudinary_storage_settings(settings, fake_cloudinary):
    """Durante el test, las fotos van a Cloudinary (falso), como en producción."""
    settings.STORAGES = {
        **settings.STORAGES,
        "default": {
            "BACKEND": "apps.core.storage.CloudinaryStorage",
            "OPTIONS": {"cloudinary_url": FAKE_CLOUDINARY_URL, "folder": "tienda-test"},
        },
    }
    return fake_cloudinary
