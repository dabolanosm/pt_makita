# Diagrama 2 — Modelo de datos (ER)

**Niveles cubiertos:** 4 (Procesamiento y almacenamiento de datos)

La aplicación persiste toda su información en una única tabla relacional `books`,
administrada por SQLAlchemy 2.x. Este diagrama muestra la estructura exacta definida en
`app/domain/models.py`, los tipos, las restricciones y el origen de cada campo (si viene
de Google Books o lo ingresa el usuario).

```mermaid
erDiagram
    BOOKS {
        INTEGER id PK "AUTOINCREMENT · autoincrement=True"
        STRING  google_id UK "UNIQUE · INDEX · nullable"
        STRING  title      "NOT NULL · volumeInfo.title o input manual"
        STRING  authors    "nullable · JSON serializado (lista)"
        STRING  publisher  "nullable · volumeInfo.publisher"
        STRING  published_date "nullable · volumeInfo.publishedDate (texto libre)"
        TEXT    description    "nullable · volumeInfo.description"
        INTEGER page_count     "nullable · volumeInfo.pageCount"
        STRING  categories     "nullable · JSON serializado (lista)"
        STRING  language       "nullable · default 'en' si no viene"
        STRING  thumbnail_url  "nullable · volumeInfo.imageLinks.thumbnail"
        STRING  preview_link   "nullable · volumeInfo.previewLink"
        DATETIME created_at     "default utcnow"
        DATETIME updated_at     "default utcnow · onupdate=utcnow"
    }
```

## Estrategia de deduplicación

- El campo `google_id` tiene constraint `UNIQUE` + `INDEX`. Es la clave de idempotencia:
  dos llamadas a `sync_from_query("python")` no crean duplicados, sino que **actualizan**
  la fila existente.
- `BookService.sync_from_query()` también aplica deduplicación **en memoria** dentro de
  la misma respuesta de Google (un `set` sobre los `google_id` de los `items` recibidos)
  para evitar inserts redundantes si la API devolviera IDs repetidos.
- Para libros creados manualmente (`POST /api/books` sin `google_id`), el campo queda
  `NULL` y se permite coexistir varios con el mismo título (no hay constraint de unicidad
  por título — es una decisión consciente, ver `docs/DECISIONS.md`).

## Estrategia de sincronización

- No hay columna `synced_at` separada. `updated_at` cubre la auditoría de cambios
  (incluyendo upserts desde Google).
- El volumen SQLite vive en `./data/app.db` y se monta como volumen Docker
  (`./data:/app/data` en `docker-compose.yml`).
- En Render free tier el filesystem es **efímero** (ver `docs/DEPLOY.md` §4): los libros
  se pierden en cada redeploy. Para producción real se recomienda PostgreSQL externo
  (Neon / Supabase) cambiando solo `DATABASE_URL`.

## Campos `JSON serializado como STRING`

`authors` y `categories` se guardan como `String` con un `json.dumps()` aplicado en
`BookService._parse_volume_info()`. Es una decisión pragmática para SQLite sin soporte
nativo de JSON, pero **es un trade-off explícito**:

- ✅ Portable: funciona igual en SQLite, Postgres y MySQL.
- ❌ No se puede consultar con `JSON` operators ni crear índices GIN.
- 🔄 Migración futura: cambiar a `JSONB` (Postgres) o `JSON` (MySQL 5.7+) según DB.

## Tablas futuras (no implementadas, referenciadas en `docs/DECISIONS.md`)

```mermaid
erDiagram
    BOOKS {
        INTEGER id PK
    }
    SYNC_LOGS {
        INTEGER id PK
        STRING  query
        INTEGER results_count
        INTEGER new_count
        INTEGER updated_count
        INTEGER elapsed_ms
        DATETIME created_at
    }
    API_ERRORS {
        INTEGER id PK
        STRING  endpoint
        INTEGER status_code
        TEXT    message
        DATETIME created_at
    }
    BOOKS ||--o{ SYNC_LOGS : "triggered by"
```

> No creadas todavía — la prueba priorizó un modelo simple y funcional. Quedan como
> "mejoras futuras" en el README.
