"""Tests del health check: los primeros tests del proyecto."""

import pytest
from django.conf import settings
from django.urls import reverse


@pytest.mark.django_db
def test_health_check_responde_ok(client):
    # Llamamos a /api/health/ como lo haría Render
    response = client.get(reverse("health"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


@pytest.mark.django_db
def test_health_check_no_acepta_post(client):
    # El health check solo sirve para leer, no para enviar datos
    response = client.post(reverse("health"))

    assert response.status_code == 405


@pytest.mark.django_db
def test_el_panel_de_admin_redirige_al_login(client):
    # Sin iniciar sesión, el panel siempre manda a la pantalla de login
    response = client.get(f"/{settings.ADMIN_URL}")

    assert response.status_code == 302
    assert "login" in response.url
