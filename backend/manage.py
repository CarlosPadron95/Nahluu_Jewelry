#!/usr/bin/env python
"""Punto de entrada de los comandos de Django (runserver, migrate, test...)."""

import os
import sys


def main():
    # Si no se indica otra cosa, en local usamos la configuración de desarrollo
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se ha podido importar Django. ¿Has activado el entorno virtual "
            "e instalado las dependencias con pip install -r requirements/dev.txt?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
