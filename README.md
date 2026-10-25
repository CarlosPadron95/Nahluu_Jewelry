# Nahluu Jewelry

Tienda online de **Nahluu Jewelry**: joyas hechas a mano en Gran Canaria en plata 925 chapada en oro. Venta a todo el mundo, en español e inglés.

> **Estado:** fase 2 de 8 (catálogo y panel de administración). La tienda todavía no está publicada.

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
│   ├── apps/           # Aplicaciones de la tienda: core (común) y catalog (catálogo)
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

Opcional: para que las fotos se guarden en Cloudinary también en local, rellena `CLOUDINARY_URL` (Cloudinary → Settings → API Keys). Si la dejas vacía, se guardan en `backend/media/`.

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

## Catálogo

Desde el panel de administración se gestionan las **categorías** (la tienda abre con Collares y Pendientes), las **colecciones** y los **productos** con sus fotos.

- Textos en español e inglés. Un producto se puede guardar como borrador a medias, pero para publicarlo necesita los textos en los dos idiomas y al menos una foto.
- Los precios se escriben en euros y se guardan en céntimos, sin errores de redondeo.
- El stock controla las etiquetas «Últimas unidades» (3 o menos) y «Agotado».
- Las fotos se giran solas, se reducen a 2560 px, se guardan en WebP y **se les quitan los metadatos EXIF**, que pueden incluir la ubicación GPS de donde se hicieron.
- Las fotos se guardan en **Cloudinary**, que las sirve desde su CDN, con una carpeta por entorno (`nahluu-local`, `nahluu`) para no mezclar pruebas y fotos reales. Producción no arranca sin Cloudinary, porque el disco de Render se borra en cada despliegue.

## API del catálogo

API pública de solo lectura que consume la web. Responde en español o en inglés: con `?lang=en`, o según la cabecera `Accept-Language` del navegador.

| Ruta | Qué devuelve |
| --- | --- |
| `GET /api/catalog/categories/` | Categorías con su número de productos publicados |
| `GET /api/catalog/collections/` | Colecciones visibles |
| `GET /api/catalog/collections/<slug>/` | Una colección |
| `GET /api/catalog/products/` | Productos publicados, por páginas de 24 |
| `GET /api/catalog/products/<slug>/` | Ficha completa, con todas las fotos y «También te puede gustar» |

Filtros de la lista de productos, que se pueden combinar: `category`, `collection`, `featured=true`, `new=true`, `q` (búsqueda sin tener en cuenta tildes ni mayúsculas), `ordering` (`featured`, `newest`, `price_asc`, `price_desc`), `page` y `page_size` (máximo 48).

- Los agotados siempre van al final.
- Nunca se envía el stock exacto, solo las etiquetas «Últimas unidades» y «Agotado».
- Los precios van en céntimos (`price_cents`) con su moneda (`currency: "EUR"`), y la web les da formato según el idioma.
- La lista hace siempre 3 consultas a la base de datos, haya los productos que haya, y un test lo comprueba.

## Flujo de trabajo

La rama `main` está protegida: no admite `push` directo ni `force push`, y solo acepta cambios que hayan pasado la CI.

1. Rama nueva para cada cambio: `git switch -c feature/nombre-del-cambio`
2. Commits pequeños con [Conventional Commits](https://www.conventionalcommits.org/es/) (`feat:`, `fix:`, `chore:`...)
3. `git push -u origin feature/nombre-del-cambio` y pull request en GitHub
4. Cuando la CI está en verde, se fusiona y se borra la rama

## Comandos útiles

| Qué | Dónde | Comando |
| --- | --- | --- |
| Tests del backend | `backend/` | `pytest` |
| Crear migraciones | `backend/` | `python manage.py makemigrations` |
| Aplicar migraciones | `backend/` | `python manage.py migrate` |
| Estilo del backend | `backend/` | `ruff check .` y `ruff format .` |
| Revisión de seguridad | `backend/` | `python manage.py check --deploy --settings=config.settings.prod` |
| Estilo del frontend | `frontend/` | `npm run lint` y `npm run format` |
| Tipos del frontend | `frontend/` | `npm run typecheck` |
| Compilar el frontend | `frontend/` | `npm run build` |

## Seguridad

- Ninguna clave se guarda en el código: todo va en archivos `.env` (ignorados por Git) y en el panel de Render.
- Los tests nunca se conectan a servicios externos: Cloudinary se sustituye por un falso que apunta lo que recibe.
- Antes de cada commit, **gitleaks** comprueba que no se sube ninguna clave por error, y GitHub Actions lo vuelve a comprobar en todo el historial.
- La configuración de producción pasa `manage.py check --deploy` sin avisos (HTTPS obligatorio, HSTS, cookies seguras).
- La web envía cabeceras de seguridad en todas las páginas.

## Derechos

© 2026 Nahluu Jewelry. Todos los derechos reservados.

El código se muestra con fines de portfolio. No está permitido copiarlo, reutilizarlo ni distribuirlo sin permiso. La marca, las fotografías y los textos pertenecen a Nahluu Jewelry.
