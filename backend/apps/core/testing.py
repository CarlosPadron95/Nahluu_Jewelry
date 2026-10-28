"""
Ayudas para los tests del panel con verificación en dos pasos.

Están en un módulo normal (y no en conftest.py) para poder importarlas
desde cualquier test.
"""

import time

from django_otp import DEVICE_ID_SESSION_KEY
from django_otp.oath import TOTP
from django_otp.plugins.otp_totp.models import TOTPDevice


def current_totp_code(device):
    """El código de 6 números que mostraría ahora mismo la app del móvil."""
    totp = TOTP(device.bin_key, device.step, device.t0, device.digits, device.drift)
    totp.time = time.time()
    return f"{totp.token():0{device.digits}d}"


def verified_client(client, user):
    """
    Inicia sesión con un usuario que ya ha pasado la verificación en dos pasos.

    Es lo mismo que haría el formulario de entrada (contraseña + código),
    pero sin escribirlos: así los tests del panel van al grano.
    """
    device, _created = TOTPDevice.objects.get_or_create(user=user, name="Móvil de pruebas")
    client.force_login(user)
    session = client.session
    session[DEVICE_ID_SESSION_KEY] = device.persistent_id
    session.save()
    return client
