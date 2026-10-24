# Nahluu Jewelry

Tienda online de **Nahluu Jewelry**: joyas hechas a mano en Gran Canaria en plata 925 chapada en oro. Venta a todo el mundo, en español e inglés.

> **Estado:** fase 1 de 8 (preparación del proyecto). La tienda todavía no está publicada.

## Tecnologías

| Parte | Tecnología | Por qué |
| --- | --- | --- |
| Frontend | [Next.js](https://nextjs.org) 16 + TypeScript | Páginas rápidas y bien posicionadas en Google |
| Backend | [Django](https://www.djangoproject.com) 5.2 LTS + Django REST Framework | API segura y panel de administración incluido |
| Base de datos | PostgreSQL 17 | Pedidos y stock fiables |
| Pagos | Stripe Checkout integrado *(fase 5)* | Los datos de tarjeta nunca pasan por nuestro servidor |
| Alojamiento | Render (Frankfurt) | Siempre encendido, copias de seguridad automáticas |
| Calidad | pytest, Ruff, ESLint, Prettier, GitHub Actions | Ningún cambio entra sin pasar los tests |

## Estructura

```
nahluu/
├── backend/            # API y panel de administración (Django)
│   ├── apps/           # Aplicaciones de la tienda (core, catálogo, pedidos...)
│   ├── config/         # Configuración: settings por entorno, rutas
│   └── requirements/   # Librerías de Python (base, dev, prod)
├── frontend/           # Web de la tienda (Next.js)
│   └── src/            # Páginas, componentes, fuentes y estilos
├── .github/            # CI (GitHub Actions) y Dependabot
└── docker-compose.yml  # Base de datos PostgreSQL para programar en local
```

## Arrancar el proyecto en local (Windows)

### Requisitos

- [Git](https://git-scm.com)
- [Python 3.13](https://www.python.org/downloads/)
- [Node.js 22 o 24 (LTS)](https://nodejs.org)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### 1. Base de datos

```powershell
docker compose up -d
```

### 2. Backend (Django), en una terminal

```powershell
cd backend
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements/dev.txt
copy .env.example .env
```

Abre `backend/.env` y rellena `DJANGO_SECRET_KEY` con una clave nueva. Para generarla:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Después:

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

- API: <http://localhost:8000/api/health/>
- Panel de administración: <http://localhost:8000/admin/>

### 3. Frontend (Next.js), en otra terminal

```powershell
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

- Web: <http://localhost:3000>

### 4. Comprobaciones antes de cada commit (una sola vez)

Con el entorno virtual del backend activado, desde la carpeta raíz del proyecto:

```powershell
pre-commit install
```

## Comandos útiles

| Qué | Dónde | Comando |
| --- | --- | --- |
| Tests del backend | `backend/` | `pytest` |
| Estilo del backend | `backend/` | `ruff check .` y `ruff format .` |
| Revisión de seguridad | `backend/` | `python manage.py check --deploy --settings=config.settings.prod` |
| Estilo del frontend | `frontend/` | `npm run lint` y `npm run format` |
| Tipos del frontend | `frontend/` | `npm run typecheck` |
| Compilar el frontend | `frontend/` | `npm run build` |

## Seguridad

- Ninguna clave se guarda en el código: todo va en archivos `.env` (ignorados por Git) y en el panel de Render.
- Antes de cada commit, **gitleaks** comprueba que no se sube ninguna clave por error, y GitHub Actions lo vuelve a comprobar en todo el historial.
- La configuración de producción pasa `manage.py check --deploy` sin avisos (HTTPS obligatorio, HSTS, cookies seguras).
- La web envía cabeceras de seguridad en todas las páginas.

## Derechos

© 2026 Nahluu Jewelry. Todos los derechos reservados.

El código se muestra con fines de portfolio. No está permitido copiarlo, reutilizarlo ni distribuirlo sin permiso. La marca, las fotografías y los textos pertenecen a Nahluu Jewelry.
