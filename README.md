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
