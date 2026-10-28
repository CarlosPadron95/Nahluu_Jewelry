"""
Tests de la seguridad del panel de administración:
verificación en dos pasos, bloqueo por intentos fallidos y permisos del equipo.
"""

import pytest
from axes.models import AccessAttempt
from django.conf import settings
from django.contrib.auth.models import Group, User
from django_otp.plugins.otp_static.models import StaticDevice
from django_otp.plugins.otp_totp.models import TOTPDevice

from apps.core.groups import SHOP_STAFF_GROUP
from apps.core.testing import current_totp_code, verified_client

ADMIN_URL = f"/{settings.ADMIN_URL}"
LOGIN_URL = f"{ADMIN_URL}login/"
PASSWORD = "una-contraseña-larga-de-prueba"


@pytest.fixture
def carlos(db):
    """Un superusuario con la app de autenticación configurada."""
    user = User.objects.create_superuser("carlos", "carlos@example.com", PASSWORD)
    TOTPDevice.objects.create(user=user, name="Móvil de Carlos")
    return user


def log_in(client, code, username="carlos", password=PASSWORD):
    """Rellena y envía el formulario de entrada del panel."""
    return client.post(
        LOGIN_URL,
        {"username": username, "password": password, "otp_token": code, "next": ADMIN_URL},
    )


# --- Verificación en dos pasos ---


def test_la_pantalla_de_entrada_pide_el_codigo(client):
    response = client.get(LOGIN_URL)

    assert response.status_code == 200
    assert "Código de verificación" in response.content.decode()


def test_entrar_con_contrasena_y_codigo_de_la_app(client, carlos):
    response = log_in(client, current_totp_code(carlos.totpdevice_set.get()))

    assert response.status_code == 302
    assert response.url == ADMIN_URL
    assert client.get(ADMIN_URL).status_code == 200


def test_sin_codigo_no_se_entra(client, carlos):
    response = log_in(client, code="")

    assert response.status_code == 200
    assert "Escribe el código de verificación" in response.content.decode()
    assert client.get(ADMIN_URL).status_code == 302  # sigue fuera


def test_con_un_codigo_incorrecto_no_se_entra(client, carlos):
    response = log_in(client, code="000000")

    assert response.status_code == 200
    assert "El código no es correcto" in response.content.decode()
    assert client.get(ADMIN_URL).status_code == 302


def test_la_contrasena_sola_no_basta(client, carlos):
    # Aunque la sesión esté iniciada, sin verificar el código no se ve el panel
    client.force_login(carlos)

    response = client.get(ADMIN_URL)

    assert response.status_code == 302
    assert "login" in response.url


def test_un_codigo_de_emergencia_sirve_una_sola_vez(client, carlos):
    device = StaticDevice.objects.create(user=carlos, name="Códigos de emergencia")
    device.token_set.create(token="emergencia1")

    first = log_in(client, code="emergencia1")
    client.logout()
    second = log_in(client, code="emergencia1")

    assert first.status_code == 302
    assert second.status_code == 200  # ya se gastó


def test_sin_la_app_configurada_se_puede_entrar_con_un_codigo_de_emergencia(client, db):
    # Así se entra la primera vez: python manage.py addstatictoken <usuario>
    nuevo = User.objects.create_superuser("nuevo", "nuevo@example.com", PASSWORD)
    device = StaticDevice.objects.create(user=nuevo, name="backup")
    device.token_set.create(token="primera1")

    right = log_in(client, code="primera1", username="nuevo")
    client.logout()
    wrong = log_in(client, code="123456", username="nuevo")

    assert right.status_code == 302
    # Con un código equivocado dice que el código no vale (no que no esté configurada)
    assert "El código no es correcto" in wrong.content.decode()


def test_no_se_puede_usar_el_movil_de_otra_persona(client, carlos):
    # Andrea tiene usuario pero aún no ha configurado su app
    User.objects.create_user("andrea", password=PASSWORD, is_staff=True)

    # Prueba con el código de la app de Carlos
    response = log_in(client, current_totp_code(carlos.totpdevice_set.get()), username="andrea")

    assert response.status_code == 200
    assert "no tiene configurada la verificación en dos pasos" in response.content.decode()


# --- Bloqueo por intentos fallidos (django-axes) ---


def test_tras_5_contrasenas_incorrectas_se_bloquea_la_cuenta(client, carlos):
    for _attempt in range(settings.AXES_FAILURE_LIMIT):
        log_in(client, code="000000", password="contraseña-equivocada")

    # Ahora, aunque la contraseña y el código sean correctos, está bloqueada
    response = log_in(client, current_totp_code(carlos.totpdevice_set.get()))

    assert response.status_code == 429
    assert "Acceso bloqueado temporalmente" in response.content.decode()
    assert client.get(ADMIN_URL).status_code == 302


def test_entrar_bien_borra_los_fallos_anteriores(client, carlos):
    log_in(client, code="000000", password="contraseña-equivocada")
    assert AccessAttempt.objects.filter(username="carlos").exists()

    log_in(client, current_totp_code(carlos.totpdevice_set.get()))

    assert not AccessAttempt.objects.filter(username="carlos").exists()


# --- Permisos del equipo de la tienda ---


def test_el_grupo_del_equipo_solo_gestiona_el_catalogo(db):
    group = Group.objects.get(name=SHOP_STAFF_GROUP)
    app_labels = set(group.permissions.values_list("content_type__app_label", flat=True))

    assert app_labels == {"catalog"}


@pytest.fixture
def andrea_client(client, db):
    """Andrea: del equipo de la tienda, sin ser superusuaria, ya verificada."""
    andrea = User.objects.create_user("andrea", password=PASSWORD, is_staff=True)
    andrea.groups.add(Group.objects.get(name=SHOP_STAFF_GROUP))
    return verified_client(client, andrea)


def test_el_equipo_puede_gestionar_productos(andrea_client):
    assert andrea_client.get(f"{ADMIN_URL}catalog/product/").status_code == 200
    assert andrea_client.get(f"{ADMIN_URL}catalog/product/add/").status_code == 200


def test_el_equipo_no_puede_tocar_usuarios_ni_la_seguridad(andrea_client):
    assert andrea_client.get(f"{ADMIN_URL}auth/user/").status_code == 403
    assert andrea_client.get(f"{ADMIN_URL}otp_totp/totpdevice/").status_code == 403
    assert andrea_client.get(f"{ADMIN_URL}axes/accessattempt/").status_code == 403
