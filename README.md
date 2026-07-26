# Book Library Sync

> Aplicación web que sincroniza libros desde la **API de Google Books** a una base de
> datos **SQLite** local, expuesta vía **API REST** (FastAPI) y una **UI ligera** (Jinja2).
> Desplegada en producción: **https://book-library-sync.onrender.com**

---

## Tabla de contenidos

1. [¿Qué es y qué problema resuelve?](#1-qué-es-y-qué-problema-resuelve)
2. [Arquitectura en 4 capas](#2-arquitectura-en-4-capas)
3. [Stack tecnológico y por qué cada pieza](#3-stack-tecnológico-y-por-qué-cada-pieza)
4. [Cómo arrancar la app desde cero](#4-cómo-arrancar-la-app-desde-cero)
5. [Cómo funciona por dentro (cold start)](#5-cómo-funciona-por-dentro-cold-start)
6. [Referencia de la API REST](#6-referencia-de-la-api-rest)
7. [Referencia de la UI web](#7-referencia-de-la-ui-web)
8. [Modelo de datos](#8-modelo-de-datos)
9. [Tests y calidad](#9-tests-y-calidad)
10. [Despliegue](#10-despliegue)
11. [Decisiones técnicas documentadas](#11-decisiones-técnicas-documentadas)
12. [Diagramas visuales](#12-diagramas-visuales)
13. [Limitaciones conocidas](#13-limitaciones-conocidas)
14. [Pendientes y roadmap](#14-pendientes-y-roadmap)
15. [Contribuir](#15-contribuir)
16. [Licencia](#16-licencia)

---

## 1. ¿Qué es y qué problema resuelve?

**Book Library Sync** es una aplicación web full-stack que resuelve un problema concreto:
tener una biblioteca local de libros consultable, sin depender de una conexión constante
a internet ni de un servicio de terceros, **pero** manteniendo la capacidad de descubrir
nuevos títulos usando una API externa reconocida (Google Books).

**Funcionalidades principales:**

- 🔍 **Buscar** libros en Google Books por título, autor o tema.
- 💾 **Sincronizar** resultados a una base SQLite local (con deduplicación por `google_id`).
- 📚 **CRUD completo** sobre la biblioteca local (crear, listar, ver detalle, editar, eliminar).
- 🗑️ **Operaciones masivas**: eliminar varios a la vez, vaciar toda la biblioteca.
- 🌐 **API REST** documentada automáticamente (Swagger en `/docs`).
- 🖥️ **UI web** server-rendered con Jinja2, modo claro/oscuro, responsive.
- 🔁 **Manejo robusto de errores** con reintentos exponenciales sobre la API externa.

**Qué NO es:**

- No es un catálogo público ni un sistema multi-usuario.
- No tiene autenticación (es una demo técnica de un solo usuario).
- No usa Pressbooks ni WordPress; es una app FastAPI autocontenida.

Para el detalle profundo de arquitectura consulta [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
Para el detalle del despliegue en Render consulta [`docs/DEPLOY.md`](docs/DEPLOY.md).

---

## 2. Arquitectura en 4 capas

El proyecto sigue una **separación estricta de responsabilidades** en cuatro capas, donde cada una cumple un propósito específico y claramente delimitado.

| Capa                | Propósito                 | Componentes principales                                                                                 | Responsabilidad                                                  |
| ------------------- | ------------------------- | ------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| **interfaces/**     | Presentación              | REST API (routers de FastAPI), Web UI (plantillas Jinja2 + JavaScript estático)                         | Traducir entre HTTP y los casos de uso del sistema.              |
| **application/**    | Aplicación / orquestación | `BookService`                                                                                           | Coordinar reglas de negocio, transacciones y deduplicación.      |
| **infrastructure/** | Infraestructura           | `HttpClient` (httpx con retry + jitter), `GoogleBooksClient`, `db.py` (engine y sessions de SQLAlchemy) | Conectar el sistema con servicios externos, red y base de datos. |
| **domain/**         | Dominio                   | `Book` (modelo ORM), `BookCreate`, `BookUpdate`, `BookRead` (schemas Pydantic)                          | Representar la entidad principal y sus reglas de negocio.        |

### Lectura rápida

* **interfaces**: recibe solicitudes y expone respuestas.
* **application**: define el flujo de ejecución.
* **infrastructure**: implementa dependencias técnicas.
* **domain**: concentra el modelo conceptual del negocio.


**Regla de dependencias:** cada capa solo puede importar de las capas inferiores.
`domain` no conoce FastAPI ni SQLAlchemy directo. `application` no conoce HTTP ni
templates. `infrastructure` no conoce routers. Esto permite cambiar la UI sin tocar
la lógica, o cambiar la DB sin tocar los casos de uso.

Para el diagrama visual completo ver
[`docs/diagrams/01-arquitectura-general.md`](docs/diagrams/01-arquitectura-general.md).

---

## 3. Stack tecnológico y por qué cada pieza

| Capa | Tecnología | Por qué se eligió | Alternativa descartada |
|---|---|---|---|
| API | **FastAPI** | Documentación OpenAPI automática, async nativo, type hints | Django (demasiado ceremonioso para este alcance), Flask (sin OpenAPI automática) |
| UI | **Jinja2** | Server-rendering, sin bundler ni SPA, perfecto para una demo | React/Vue (requieren npm build, overkill para una biblioteca personal) |
| HTTP | **httpx** | Cliente async moderno, mismo API que `requests`, soporte de timeouts | `requests` (solo sync), `aiohttp` (API menos pythonica) |
| ORM | **SQLAlchemy 2.x** | Maduro, tipado, mismo código funciona en SQLite y Postgres | Tortoise ORM (menos adopción), SQLModel (más nuevo, sin avantage real aquí) |
| DB | **SQLite** | Cero infraestructura, archivo local, perfecto para demo | PostgreSQL (necesita servidor), MongoDB (no relacional) |
| Validación | **Pydantic v2** | Schemas declarativos, validación automática, type hints | Marshmallow (más código), dataclasses (sin validación) |
| Config | **pydantic-settings** | Variables de entorno tipadas, con `.env` | `os.getenv` (sin tipos), `python-decouple` (menos pythonico) |
| Deploy | **Render.com** | Plan free, Docker nativo, HTTPS auto, CI/CD por git push | Railway (sin free tier), Fly.io (más config), Cloud Run (requiere GCP) |

**Justificación detallada** de cada decisión (incluyendo la decisión de **no usar
Pressbooks** y de **eliminar el caché en memoria** que tenía un bug) en
[`docs/DECISIONS.md`](docs/DECISIONS.md).

---

## 4. Cómo arrancar la app desde cero

### 4.1. Prerrequisitos

- **Docker Desktop** instalado y corriendo (Docker Engine 24+).
- **Git** para clonar el repositorio.
- Una **API key de Google Books** (gratis): https://console.cloud.google.com/ →
  crear proyecto → habilitar "Books API" → crear credencial "API key".
  La key debe estar **restringida a "Books API"** o devolverá 403.

### 4.2. Setup local

```bash
# 1. Clonar
git clone https://github.com/dabolanosm/pt_makita.git
cd pt_makita

# 2. Configurar variables de entorno
cp .env.example .env
# Edita .env y rellena GOOGLE_BOOKS_API_KEY con tu key real
# (los demás valores ya tienen defaults razonables)

# 3. Levantar
docker compose up --build -d

# 4. Verificar
curl http://localhost:8000/health
# Esperado: {"status":"ok","version":"0.1.0"}
```

### 4.3. Verificación visual

Abre en el navegador:

| URL | Qué verás |
|---|---|
| `http://localhost:8000/` | Dashboard de la biblioteca (vacía al inicio) |
| `http://localhost:8000/docs` | Swagger UI con todos los endpoints documentados |
| `http://localhost:8000/redoc` | ReDoc (alternativa a Swagger) |
| `http://localhost:8000/health` | Health check (JSON) |
| `http://localhost:8000/health/db` | Health check de la DB |

### 4.4. Sincronización inicial

La base de datos arranca **vacía** (solo con el schema). Para llenarla:

```bash
# Sincronizar las 6 búsquedas semilla (python, sci-fi, colombia, etc.)
curl -X POST "http://localhost:8000/api/sync/seed?confirm=true"

# O una búsqueda específica
curl -X POST http://localhost:8000/api/sync \
  -H "Content-Type: application/json" \
  -d '{"query":"python programming","max_results":5}'
```

O usa los botones de búsqueda rápida del dashboard en `http://localhost:8000/`.

---

## 5. Cómo funciona por dentro (cold start)

Esta sección explica **qué pasa desde que ejecutas `docker compose up` hasta que la app
responde al primer request**, con el detalle exacto de cada paso. Es importante entenderlo
para saber por qué SQLite arranca vacío y cuándo se crean los archivos.

### Paso 1 — Build de la imagen Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

Docker construye una imagen basada en `python:3.12-slim`, instala las dependencias de
`requirements.txt` y copia el código fuente a `/app`. El `CMD` define que el proceso
principal será `uvicorn` con auto-reload (útil en desarrollo).

### Paso 2 — Inicio del contenedor

`docker compose up` arranca el servicio `api` mapeando:
- `./:/app` → bind volume con el código (cambios en caliente con `--reload`).
- `./data:/app/data` → bind volume con la base de datos (persiste en el host).
- `env_file: .env` → carga `GOOGLE_BOOKS_API_KEY` y demás configuración.

### Paso 3 — uvicorn carga la app

`uvicorn` importa `app/main.py` y ejecuta la función `create_app()`. Esta función:

1. Crea la instancia de `FastAPI(title="Book Library Sync", version="0.1.0", lifespan=...)`.
2. Monta `/static` para servir `app.js` y `styles.css`.
3. Registra 4 exception handlers (`ExternalAPIError`, `NotFoundError`, `ValidationError`,
   `RequestValidationError`) que traducen excepciones a respuestas JSON consistentes.
4. Registra un middleware HTTP que loggea método, path, status y duración de cada request.
5. Incluye los routers: `health_router`, `books_router` (con prefijo `/api`),
   `sync_router` (con prefijo `/api`), `web_router` (sin prefijo).

### Paso 4 — Lifespan startup: se crea la base de datos

Antes de aceptar el primer request, FastAPI ejecuta el hook de `lifespan`:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(...)
    init_db()        # ← aquí
    yield
```

`init_db()` ejecuta `Base.metadata.create_all(engine)`, lo cual:
- **Crea el archivo `data/app.db`** si no existe.
- **Crea la tabla `books`** con sus 14 columnas, PK, índices y constraints.
- **NO inserta ninguna fila.** La base queda completamente vacía.

> ⚠️ **SQLite arranca vacío.** Solo con el schema. La única forma de llenarlo es
> llamar a `POST /api/sync` (sincronización desde Google Books) o a `POST /api/books`
> (creación manual). En Render free tier, el archivo es **efímero** y se borra en
> cada redeploy. Ver [`docs/DEPLOY.md` §4](docs/DEPLOY.md) para más detalle.

### Paso 5 — uvicorn queda escuchando

La app queda escuchando en `0.0.0.0:8000`. Ya está lista para recibir requests.

### Paso 6 — Primer request: el camino completo

Tomemos como ejemplo un `GET /` (abrir el dashboard):

```
[Browser]
    │
    │  GET /  HTTP/1.1
    │  Host: localhost:8000
    ▼
[Middleware: log_requests]
    │  log "Request start GET /"
    ▼
[FastAPI router]
    │  Resuelve ruta "/" → routes.home()
    │  Resuelve Depends: get_db() y get_book_service()
    ▼
[get_db]
    │  Abre sesión SQLAlchemy: SessionLocal()
    │  yield session
    ▼
[get_book_service]
    │  settings = get_settings()           ← lee .env
    │  client = GoogleBooksClient(api_key) ← crea cliente HTTP
    │  service = BookService(db, client)  ← instancia del servicio
    │  return service
    ▼
[routes.home]
    │  books = service.list_books()        ← SELECT * FROM books
    │  → []  (vacío la primera vez)
    │  rendered = templates.TemplateResponse("index.html", {...})
    ▼
[Jinja2]
    │  Renderiza base.html + index.html
    │  books = [] → muestra empty state
    ▼
[Middleware: log_requests]
    │  log "Request end GET / status=200 duration_ms=X"
    ▼
[Browser]
    Recibe HTML con la página vacía
```

**Observación importante:** `BookService` se crea **por cada request**. Esto significa
que cualquier caché basado en atributos de instancia (como tenía originalmente) sería
inútil. Esa es la razón por la que se eliminó el caché. Ver
[`docs/DECISIONS.md`](docs/DECISIONS.md) para el detalle.

---

## 6. Referencia de la API REST

Todos los endpoints están bajo `/api/*` excepto los health checks. La documentación
interactiva (Swagger UI con try-it-out) está disponible en **`/docs`**, y la
especificación OpenAPI en JSON en **`/openapi.json`**.

### 6.1. Health checks

| Método | Ruta | Descripción | Respuestas |
|---|---|---|---|
| `GET` | `/health` | Verifica que la app está viva **y** que la API key de Google está configurada | `200 {"status":"ok"}` · `500` si falta la key |
| `GET` | `/health/db` | Ejecuta `SELECT 1` para confirmar la conexión a SQLite | `200 {"status":"ok","database":"connected"}` · `500` si DB caída |

### 6.2. CRUD de libros

| Método | Ruta | Descripción | Códigos |
|---|---|---|---|
| `GET` | `/api/books` | Lista todos los libros guardados (sin paginación, los devuelve todos) | `200` |
| `GET` | `/api/books/{id}` | Devuelve un libro específico por su ID | `200` · `404` si no existe |
| `POST` | `/api/books` | Crea un libro manualmente (sin pasar por Google Books) | `201` + BookRead · `422` si payload inválido |
| `PUT` | `/api/books/{id}` | Actualiza campos parciales (PATCH-like; solo los campos enviados) | `200` · `404` · `422` |
| `DELETE` | `/api/books/{id}` | Elimina un libro específico | `204` (sin body) · `404` |
| `DELETE` | `/api/books` | Elimina TODOS los libros (devuelve `{deleted: N}`) | `200` |

**Ejemplo de payload para `POST /api/books`:**

```json
{
  "title": "Clean Code",
  "authors": "Robert C. Martin",
  "publisher": "Prentice Hall",
  "published_date": "2008",
  "description": "A handbook of agile software craftsmanship.",
  "page_count": 464,
  "categories": "Programming, Software Engineering",
  "language": "en",
  "thumbnail_url": "https://...",
  "preview_link": "https://books.google.com/..."
}
```

### 6.3. Sincronización con Google Books

| Método | Ruta | Descripción | Códigos |
|---|---|---|---|
| `POST` | `/api/sync` | Sincroniza desde Google Books con una query arbitraria | `200` · `422` si `max_results > 10` · `502` si Google falla |
| `POST` | `/api/sync/seed?confirm=true` | Sincroniza las 6 búsquedas semilla (python, sci-fi, colombia, etc.) | `200` · `422` sin `confirm=true` · `502` si alguna falla |

> Nota: Google Books puede devolver errores 503 o 5xx por saturación o mantenimiento temporal de su servicio. La app reintenta de forma exponencial y, si el fallo persiste, termina respondiendo con `502` como `ExternalAPIError`.

**Ejemplo para `POST /api/sync`:**

```json
{
  "query": "python programming",
  "max_results": 5
}
```

**Ejemplo curl:**

```bash
curl -X POST http://localhost:8000/api/sync \
  -H "Content-Type: application/json" \
  -d '{"query":"python programming","max_results":5}'
```

**Qué hace internamente** (ver [`docs/diagrams/03-flujo-sincronizacion.md`](docs/diagrams/03-flujo-sincronizacion.md)):

1. Valida `max_results ≤ 10` (Pydantic + verificación interna).
2. Llama a `GoogleBooksClient.search(query, max_results)`.
3. Aplica dedup en memoria (set de `google_id`).
4. Para cada item: `SELECT WHERE google_id = ?` → INSERT si nuevo, UPDATE si existe.
5. `db.commit()` al final (atómico; rollback si algo falla).
6. Loggea métricas: `query · results · new · updated · elapsed_ms`.

### 6.4. Sistema de errores

Todas las respuestas de error siguen el mismo formato JSON:

```json
{
  "detail": "Mensaje legible del error",
  "type": "ExternalAPIError"
}
```

Excepciones custom definidas en `app/errors.py`:

| Excepción | status_code por defecto | Cuándo se lanza |
|---|---|---|
| `ExternalAPIError` | 502 | Fallo en llamada a Google Books (red, 4xx, 5xx, agotar reintentos) |
| `NotFoundError` | 404 | Recurso no encontrado (libro, etc.) |
| `ValidationError` | 422 | Error de validación de negocio (ej. sync/seed sin `confirm=true`) |

---

## 7. Referencia de la UI web

La UI está implementada con **Jinja2 templates** servidos desde `app/interfaces/web/`.
Usa JavaScript vanilla (sin frameworks) para interactividad local (toasts, modales,
tema, multi-select).

### 7.1. Rutas web

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/` | Dashboard principal: biblioteca + búsquedas + seeds + toasts |
| `GET` | `/books/{id}` | Página de detalle de un libro |
| `POST` | `/web/sync` | Sincroniza con una query arbitraria (envía `query` como form field) |
| `POST` | `/web/sync/{query}` | Atajo desde las búsquedas semilla (query en la URL) |
| `POST` | `/web/search/local` | Busca en la biblioteca local (título, autor o categoría) |
| `POST` | `/web/search/google` | Busca en Google Books sin guardar |
| `POST` | `/web/books/add` | Agrega un libro por `google_id` (form field) |
| `POST` | `/web/books/{id}/delete` | Elimina un libro desde la card |
| `POST` | `/web/books/delete-selected` | Elimina varios libros (envía `selected_ids` como form field array) |
| `POST` | `/web/library/clear` | Vacía toda la biblioteca (requiere confirmación) |

### 7.2. Características de la UI

- **Modo claro/oscuro** persistente en `localStorage`, respeta `prefers-color-scheme`.
- **Multi-select** de libros con toolbar flotante que aparece al seleccionar.
- **Toasts** con auto-dismiss (3.5s) y barra de progreso visual.
- **Modales** de confirmación (eliminar libro, limpiar biblioteca) con cierre por backdrop o ESC.
- **Loading states** en todos los forms: el botón se deshabilita y muestra un spinner.
- **Empty state** ilustrado cuando la biblioteca está vacía.
- **Responsive** mobile-first con breakpoints en 640/768/1024/1280px.

---

## 8. Modelo de datos

Una única tabla relacional definida en `app/domain/models.py`:

```python
class Book(Base):
    __tablename__ = "books"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    google_id: Mapped[str | None] = mapped_column(String, unique=True, index=True, nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    authors: Mapped[str | None] = mapped_column(String, nullable=True)
    publisher: Mapped[str | None] = mapped_column(String, nullable=True)
    published_date: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    categories: Mapped[str | None] = mapped_column(String, nullable=True)
    language: Mapped[str | None] = mapped_column(String, nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String, nullable=True)
    preview_link: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Puntos clave:**

- `google_id` es la **clave de idempotencia**: UNIQUE + INDEX. Dos llamadas a
  `sync_from_query("python")` no crean duplicados; la segunda actualiza.
- `authors` y `categories` se guardan como **String con JSON serializado** (trade-off
  documentado en DECISIONS: portable pero no queryable como JSON nativo).
- `created_at` y `updated_at` se gestionan automáticamente vía SQLAlchemy.
- No hay tabla de auditoría ni de logs de sync (mejora futura).

Para el diagrama ER completo ver
[`docs/diagrams/02-modelo-datos.md`](docs/diagrams/02-modelo-datos.md).

---

## 9. Tests y calidad

### 9.1. Ejecutar los tests

```bash
# Local con Docker
docker compose run --rm api pytest

# Local sin Docker (requiere Python 3.12 + pip install -r requirements.txt + pip install pytest pytest-asyncio)
pytest -v
```

### 9.2. Cobertura actual

Hay 3 archivos de tests cubriendo los flujos principales:

| Archivo | Cubre |
|---|---|
| `tests/test_api.py` | Endpoints REST (`/api/books` CRUD) con cliente de tests y DB en memoria |
| `tests/test_book_service.py` | Lógica de `BookService`: CRUD + sync + dedup + reintentos |
| `tests/test_books_client.py` | `GoogleBooksClient.search()` con `httpx.Response` mockeado |

### 9.3. CI/CD

Cada `git push` a `main` dispara **GitHub Actions** (`.github/workflows/test.yml`)
que ejecuta la suite completa en Python 3.12. El badge de estado aparecerá en la
página del repo cuando se active GitHub Actions.

Para ejecutarlo localmente antes de pushear:

```bash
GOOGLE_BOOKS_API_KEY=test-key pytest -q
```

---

## 10. Despliegue

### 10.1. Local con Docker Compose

```bash
docker compose up --build -d
```

- El servicio `api` se construye desde el `Dockerfile`.
- El código se monta como bind volume (cambios en caliente).
- `data/app.db` se monta en `./data` (persiste en el host).

### 10.2. Producción en Render.com

La app está desplegada en **https://book-library-sync.onrender.com** usando la
configuración de `render.yaml` (Render Blueprint).

**Por qué Render:**

- Plan gratuito funcional.
- Lee el `Dockerfile` directamente, sin adaptadores.
- HTTPS automático con certificado válido.
- Auto-deploy desde GitHub en cada `push` a `main`.

**Limitaciones del plan gratuito** (importantes):

- **Cold start**: la app "duerme" tras 15 min sin tráfico. El siguiente request
  tarda 30-50 s extra mientras arranca.
- **Filesystem efímero**: `data/app.db` se **borra** en cada redeploy. Los libros
  sincronizados se pierden.
- Solo dominio `*.onrender.com` (no se puede custom domain en plan free).

**Soluciones para persistencia** (ver [`docs/DEPLOY.md` §5](docs/DEPLOY.md)):

- **Opción A**: Render Persistent Disk (1 USD/mes, requiere plan starter).
- **Opción B**: PostgreSQL externo gratuito (Neon.tech o Supabase) + cambiar `DATABASE_URL`.

**Para hacer tu propio deploy** ver [`docs/DEPLOY.md`](docs/DEPLOY.md) — guía paso
a paso con troubleshooting completo.

---

## 11. Decisiones técnicas documentadas

Las decisiones de diseño (incluyendo las que NO se implementaron y por qué) están
documentadas en [`docs/DECISIONS.md`](docs/DECISIONS.md). Algunas especialmente
importantes:

- **Por qué FastAPI y no Django/Flask** → liviano, OpenAPI auto, async nativo.
- **Por qué SQLite y no Postgres** → cero infra, perfecto para demo local.
- **Por qué Jinja2 y no React/Vue** → sin bundler, sin npm, foco en backend.
- **Por qué NO se usó Pressbooks** → PHP+MySQL añade 1.5 GB RAM y ~1 min de bootstrap
  que no aportan al núcleo de la evaluación. La integración posterior sería vía plugin
  WP con un shortcode que consuma `/api/books`.
- **Por qué se eliminó el caché de `BookService`** → con el wiring actual de FastAPI
  (`Depends(get_book_service)` por request), el caché basado en `self._query_cache`
  se reiniciaba en cada request, haciendo inútil el TTL de 60 s. Se prefirió eliminar
  el código muerto a tener un caché mentiroso.
- **Por qué se diseñó la UI con un sistema visual propio** → mantener el control
  total sin dependencias de CSS/JS externos. Ver sección de autocrítica en DECISIONS.

---

## 12. Diagramas visuales

Toda la documentación visual está en [`docs/diagrams/`](docs/diagrams/README.md)
escrita en Mermaid (se renderiza nativa en GitHub):

| # | Diagrama | Qué muestra | Niveles cubiertos |
|---|---|---|---|
| 1 | [Arquitectura general](docs/diagrams/01-arquitectura-general.md) | Las 4 capas + browser + Google Books + SQLite | 1 · 2 · 5 · 6 |
| 2 | [Modelo de datos (ER)](docs/diagrams/02-modelo-datos.md) | Tabla `books` con sus 14 columnas y constraints | 4 |
| 3 | [Flujo de sincronización](docs/diagrams/03-flujo-sincronizacion.md) | Flujograma del `POST /api/sync` con reintentos, dedup, errores | 3 · 4 · 6 |
| 4 | [Secuencia UML del sync](docs/diagrams/04-secuencia-sync.md) | Orden temporal de llamadas + variantes (`/sync/seed`, `/web/sync`) | 3 · 6 |
| 5 | [Despliegue](docs/diagrams/05-despliegue.md) | Local dev vs Render free tier vs topología futura con Postgres | 1 · 7 |

**Recomendación de lectura:**

- ¿Primera vez? → empieza por el 1.
- ¿Solo te importa la DB? → salta al 2.
- ¿Te importa la lógica de sync? → lee el 3 (flujo) **y** el 4 (orden temporal). Son complementarios.
- ¿Te importa el deploy? → ve directo al 5.

---

## 13. Limitaciones conocidas

- **Sin paginación en `GET /api/books`**: devuelve todos los libros. Para < 1000 libros
  no es problema; para más, agregar `?skip=N&limit=M` (trivial).
- **Sin autenticación**: la API es pública. En producción real agregar API key o JWT.
- **Sin protección CSRF completa**: los forms web confían en SameSite cookies del browser.
- **SQLite efímero en Render free tier**: ver §10.2.
- **`max_results` limitado a 10** por Google Books en la implementación actual.
  Es un limit hard en Pydantic + verificación interna.
- **Sin tests E2E**: solo unitarios e integración. Faltan tests con Playwright/Selenium.
- **Sin rate limiting**: un cliente puede agotar la cuota de Google Books.
- **`authors` y `categories` como String JSON**: no queryable como JSON nativo (trade-off).

---

## 14. Pendientes y roadmap

Listados en orden de impacto:

1. 🔴 **Persistencia real en producción** (Postgres externo o Persistent Disk de Render).
2. 🔴 **Autenticación** (API key estática para `/api/*` o JWT).
3. 🟡 **Paginación** en `GET /api/books`.
4. 🟡 **Rate limiting** con `slowapi` para proteger la cuota de Google Books.
5. 🟡 **Tests E2E** con Playwright sobre la UI web.
6. 🟢 **Cache real** (Redis o módulo singleton) si el tráfico lo justifica.
7. 🟢 **Tabla de auditoría** `sync_logs` con métricas por request.
8. 🟢 **CI más completo**: linting con `ruff`, type-check con `mypy`, coverage report.
9. 🟢 **Webhook de Google Books** para sync incremental en lugar de polling.
10. 🟢 **Soporte multi-idioma** (i18n con `gettext`).

---

## 15. Contribuir

1. Fork el repo.
2. Crea una rama: `git checkout -b feature/mi-cambio`.
3. Haz commits descriptivos.
4. Asegúrate de que los tests pasan: `pytest -v`.
5. Push y abre un Pull Request describiendo el cambio.

**Convenciones de código:**

- Python: `ruff` para linting, type hints en todo el código nuevo.
- Commits: conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`).
- Idioma del código: inglés. Idioma de docs y UI: español.
- Estilo: seguir las convenciones de cada framework (FastAPI, SQLAlchemy, Jinja2).

---

## 16. Licencia

MIT License — ver [`LICENSE`](LICENSE) para el texto completo. Puedes usar, modificar
y distribuir este software libremente con solo mantener el aviso de copyright original.
