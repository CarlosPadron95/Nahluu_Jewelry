"""
Panel de administración con verificación en dos pasos (2FA).

Para entrar hacen falta DOS cosas:
1. El usuario y la contraseña (algo que sabes).
2. El código de 6 números de la app de autenticación del móvil
   (algo que tienes). Cambia cada 30 segundos.

Así, aunque alguien robe la contraseña, no puede entrar sin el móvil.
Si se pierde el móvil, se puede entrar con un código de emergencia
(se crean con: python manage.py addstatictoken <usuario>).
"""

from django import forms
from django_otp.admin import OTPAdminAuthenticationForm, OTPAdminSite
from django_otp.forms import OTPAuthenticationFormMixin
from django_otp.plugins.otp_static.models import StaticDevice
from django_otp.plugins.otp_totp.models import TOTPDevice


class TwoFactorLoginForm(OTPAdminAuthenticationForm):
    """
    Formulario de entrada al panel: usuario, contraseña y código.

    django-otp pide elegir el "dispositivo" (la app del móvil o los códigos
    de emergencia) en una lista. Para que sea más sencillo, lo elegimos solos:
    - si el código son solo números y el usuario tiene la app, es el de la app;
    - si no, probamos con sus códigos de emergencia.
    Solo se prueba UN dispositivo: así un fallo no bloquea a los demás.
    """

    otp_token = forms.CharField(
        label="Código de verificación",
        required=False,
        widget=forms.TextInput(
            # one-time-code: el móvil puede sugerir el código automáticamente
            attrs={"autocomplete": "one-time-code", "autocapitalize": "none"}
        ),
    )

    # Mensajes de error más claros que los que trae django-otp
    otp_error_messages = {
        **OTPAuthenticationFormMixin.otp_error_messages,
        "token_required": "Escribe el código de verificación de tu app de autenticación.",
        "invalid_token": "El código no es correcto o ha caducado. Prueba con el siguiente.",
        "device_required": (
            "Esta cuenta no tiene configurada la verificación en dos pasos. "
            "Pide ayuda a quien administra la tienda."
        ),
    }

    def _chosen_device(self, user):
        token = (self.cleaned_data.get("otp_token") or "").strip()
        if not token:
            return None

        # Solo buscamos entre los dispositivos de ESTE usuario y ya confirmados
        phone_app = TOTPDevice.objects.filter(user=user, confirmed=True).first()
        backup_codes = StaticDevice.objects.filter(user=user, confirmed=True).first()

        if token.isdigit() and phone_app:
            return phone_app
        # Si no tiene ninguno de los dos, devuelve None y se muestra
        # el mensaje "no tiene configurada la verificación en dos pasos"
        return backup_codes or phone_app


class NahluuAdminSite(OTPAdminSite):
    """Panel de la tienda: solo entra quien supera la verificación en dos pasos."""

    site_header = "Nahluu Jewelry · Administración"
    site_title = "Nahluu Jewelry"
    index_title = "Panel de la tienda"

    login_form = TwoFactorLoginForm
    login_template = "admin/login_2fa.html"

    def __init__(self, name="admin"):
        # Mantenemos el nombre "admin" para que las rutas sigan siendo admin:...
        super().__init__(name)
