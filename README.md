# Book Library Sync

## Descripción general

Book Library Sync es una aplicación web que sincroniza libros desde la API de Google Books y los guarda en una biblioteca local. Permite buscar colecciones de libros, revisar el detalle de cada título y eliminar entradas de forma sencilla.

La aplicación ofrece una API REST para operaciones CRUD y sincronización, junto con una interfaz web ligera construida en Jinja2.

## Arquitectura

La aplicación está organizada en cuatro capas:

- `domain`: modelos de dominio y esquemas Pydantic.
- `infrastructure`: cliente HTTP, acceso a Google Books y conexión a SQLite.
- `application`: lógica de negocio en `BookService`.
- `interfaces`: API REST y UI web.

Ver también `docs/ARCHITECTURE.md`.

## Stack tecnológico

| Capa | Tecnología | Por qué |
|---|---|---|
| API | FastAPI | Documentación automática y desarrollo rápido |
| UI | Jinja2 | Renderizado de plantillas simple sin frontend SPA |
| HTTP | httpx | Cliente async moderno con timeout y reintentos |
| ORM | SQLAlchemy 2.x | Mapeo ORM robusto compatible con SQLite |
| DB | SQLite | Persistencia local ligera y sin servidor |

## Requisitos previos

- Docker Desktop
- Git
- Una API key de Google Books

## Configuración

1. Clona el repositorio.
2. Copia `.env.example` a `.env`.
3. Rellena `GOOGLE_BOOKS_API_KEY` con tu clave de Google Books.
4. Ajusta otras variables si es necesario.

## Instalación y ejecución

```bash
docker compose up --build -d
```

## Endpoints de la API

| Método | Ruta | Descripción | Ejemplo |
|---|---|---|---|
| GET | `/health` | Verifica que la app está viva | `curl http://localhost:8000/health` |
| GET | `/health/db` | Verifica la conexión a la base de datos | `curl http://localhost:8000/health/db` |
| GET | `/api/books` | Lista libros guardados | `curl http://localhost:8000/api/books` |
| GET | `/api/books/{id}` | Detalle de un libro | `curl http://localhost:8000/api/books/1` |
| POST | `/api/books` | Crea un libro manual | `curl -X POST http://localhost:8000/api/books -H "Content-Type: application/json" -d '{"title":"Nuevo Libro"}'` |
| PUT | `/api/books/{id}` | Actualiza un libro | `curl -X PUT http://localhost:8000/api/books/1 -H "Content-Type: application/json" -d '{"title":"Actualizado"}'` |
| DELETE | `/api/books/{id}` | Elimina un libro | `curl -X DELETE http://localhost:8000/api/books/1` |
| POST | `/api/sync` | Sincroniza desde Google Books | `curl -X POST http://localhost:8000/api/sync -H "Content-Type: application/json" -d '{"query":"python","max_results":5}'` |
| POST | `/api/sync/seed?confirm=true` | Sincroniza búsquedas semilla | `curl -X POST http://localhost:8000/api/sync/seed?confirm=true` |

## Endpoints web

- `GET /` — dashboard web
- `GET /books/{id}` — detalle del libro

## Modelo de datos

Tabla `books`:

- `id`: PK
- `google_id`: ID externo de Google Books
- `title`
- `authors`
- `publisher`
- `published_date`
- `description`
- `page_count`
- `categories`
- `language`
- `thumbnail_url`
- `preview_link`
- `created_at`
- `updated_at`

## Búsquedas semilla

- Programación Python — `python programming`
- Ciencia ficción — `science fiction`
- Historia de Colombia — `colombia history`
- Literatura latinoamericana — `latin american literature`
- Desarrollo web — `web development`
- Inteligencia artificial — `artificial intelligence`

## Pruebas

```bash
docker compose run --rm api pytest
```

## Decisiones técnicas

- Se eligió Google Books para tener una API de libros estable y sin OAuth para búsquedas básicas.
- Se eligió FastAPI por su velocidad y documentación automática.
- Se eligió SQLite para facilitar la ejecución local sin infraestructura adicional.
- Se eligió Jinja2 para una UI simple sin necesidad de bundlers o SPA.
- No se implementó protección CSRF completa, ya que excede el alcance de la prueba técnica.

## Limitaciones conocidas

- No hay paginación en la UI.
- No hay cache de resultados.
- No hay protección CSRF completa.
- La UI es básica y no tiene autenticación.

## Problemas encontrados

- Hubo problemas iniciales con Docker Desktop no conectado al daemon local.
- Se asumió que la API key de Google Books está habilitada correctamente.

## Aspectos pendientes / Mejoras futuras

- Añadir tests end-to-end reales.
- Agregar paginación y búsqueda en la UI.
- Añadir cache de resultados.
- Mejorar handling de cuotas de Google Books.

## Proceso de despliegue

En un VPS se puede desplegar con Docker Compose, exponiendo el servicio en el puerto 8000 y montando el volumen `data/` para persistencia. Para producción se recomienda usar un proxy inverso con TLS.

## Publicación en la nube (Nivel 7) ✅

La aplicación está desplegada y accesible públicamente en:

**🔗 https://book-library-sync.onrender.com**

> Nota: al primer request la app puede tardar 30-50 segundos (cold start del plan gratuito de Render). Los requests siguientes son normales.

### Plataforma utilizada

**Render.com** (plan gratuito) — fue elegida porque:

- Detecta y construye el `Dockerfile` automáticamente (cero código nuevo).
- HTTPS automático con certificado válido.
- Plan gratuito funcional para demos.
- Redespliegue automático con cada `git push` (CI/CD gratis).

### Cómo se hizo (sin modificar el código fuente)

1. Se añadió un único archivo de configuración: `render.yaml` (Render Blueprint). Este archivo declara el servicio web, las variables de entorno y un override del comando de inicio para producción (`uvicorn ... --port $PORT` en vez de `--reload`).
2. Se añadió `docs/DEPLOY.md` con la guía paso a paso y troubleshooting.
3. Se conectó el repo de GitHub a Render.
4. Se configuró la variable de entorno secreta `GOOGLE_BOOKS_API_KEY` en el dashboard de Render.
5. Render construyó la imagen Docker con el `Dockerfile` original del proyecto y la desplegó.

**No se modificó ningún archivo del código fuente** (`app/`, `tests/`, `scripts/`, etc.). El `Dockerfile` y `docker-compose.yml` originales quedan intactos.

### Limitaciones del plan gratuito

- La app "duerme" tras 15 minutos sin tráfico (cold start en el siguiente request).
- El archivo SQLite es **efímero**: los libros sincronizados se borran al redeploy. Si necesitas persistencia, consulta `docs/DEPLOY.md` sección 5 (Persistent Disk por 1 USD/mes, o PostgreSQL externo gratuito).
- Solo dominio `*.onrender.com` (sin dominio personalizado en el plan free).

### Verificación rápida

Una vez en línea, prueba:

| URL | Esperado |
|---|---|
| `/` | Dashboard con la biblioteca |
| `/docs` | Swagger UI con todos los endpoints |
| `/health` | `{"status":"ok"}` |
| `/api/books` | Lista de libros (vacía al inicio) |

### Guía detallada

Ver [`docs/DEPLOY.md`](docs/DEPLOY.md) para instrucciones paso a paso, troubleshooting completo y alternativas (Railway, Fly.io, Cloud Run).
