"""Vistas comunes de la API."""

from django.db import connection
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """
    Comprueba que el backend está vivo y que llega a la base de datos.

    Render llama a esta ruta cada poco tiempo: si no responde "ok",
    sabe que algo va mal y no manda visitas a esa versión.
    """

    # Esta ruta es pública: no hace falta iniciar sesión
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            # Una consulta mínima para saber si la base de datos responde
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            database_ok = True
        except Exception:
            database_ok = False

        if database_ok:
            return Response({"status": "ok", "database": "ok"})
        return Response({"status": "error", "database": "error"}, status=503)
