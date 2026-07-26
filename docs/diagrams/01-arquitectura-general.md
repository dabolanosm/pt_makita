# Diagrama 1 — Arquitectura general (4 capas)

**Niveles cubiertos:** 1 (Docker) · 2 (Aplicación principal) · 5 (API propia) · 6 (Integración)

Este diagrama muestra cómo se organizan los componentes de **Book Library Sync** y cómo
interactúan entre sí. Refleja la separación en cuatro capas implementada en `app/`:

- `domain` → modelos y esquemas Pydantic (sin dependencias externas).
- `infrastructure` → SQLAlchemy, `HttpClient`, `GoogleBooksClient`.
- `application` → `BookService` (orquesta casos de uso).
- `interfaces` → routers REST (`/api/*`) y rutas web (Jinja2).

Los tres caminos de entrada (UI web, API REST, sync externo) convergen en `BookService`,
que es la única capa que toca tanto la base de datos local como la API externa.

```mermaid
flowchart TB
    subgraph CLIENTS["Clientes"]
        direction LR
        Browser["🖥️ Navegador<br/>(Jinja2 templates)"]
        APIConsumer["📡 Cliente REST<br/>(curl / Postman / SDK)"]
    end

    subgraph INTERFACES["interfaces/ — Capa de presentación"]
        direction TB
        WebRouter["Web Router<br/>(routes.py)<br/>GET / · GET /books/{id}<br/>POST /web/sync · /web/search/*"]
        APIRouter["API Router<br/>(books.py · sync.py · health.py)<br/>/api/books · /api/sync · /health"]
    end

    subgraph APPLICATION["application/ — Capa de aplicación"]
        BookService["📚 BookService<br/>· list_books()<br/>· get_book()<br/>· create_book()<br/>· update_book()<br/>· delete_book()<br/>· search_local()<br/>· search_books()<br/>· sync_from_query()<br/>🗃️ caché de consultas (TTL 60s)"]
    end

    subgraph INFRASTRUCTURE["infrastructure/ — Capa de infraestructura"]
        direction TB
        GoogleBooksClient["GoogleBooksClient<br/>· search(q, max_results)<br/>· get_by_id(volume_id)"]
        HttpClient["HttpClient (httpx)<br/>· timeouts configurables<br/>· reintentos con backoff<br/>  y jitter (1s, 2s, 4s)"]
        DBEngine[("SQLAlchemy engine<br/>+ SessionLocal<br/>+ get_db()")]
    end

    subgraph DOMAIN["domain/ — Capa de dominio"]
        direction TB
        BookModel["Book (ORM)<br/>· 14 columnas<br/>· tabla books"]
        Schemas["Pydantic Schemas<br/>· BookCreate<br/>· BookUpdate<br/>· BookRead"]
    end

    subgraph EXTERNAL["Servicios externos"]
        GoogleAPI["🌐 Google Books API<br/>www.googleapis.com/books/v1"]
        SQLite[("📁 SQLite<br/>data/app.db<br/>(volumen Docker)")]
    end

    %% Flujos UI
    Browser -->|"GET / · POST /web/*"| WebRouter
    WebRouter -->|"BookService (Depends)"| BookService

    %% Flujos API
    APIConsumer -->|"GET · POST · PUT · DELETE"| APIRouter
    APIRouter -->|"BookService (Depends)"| BookService

    %% BookService ↔ infrastructure
    BookService -->|"search() · get_by_id()"| GoogleBooksClient
    GoogleBooksClient -->|"GET volumes · GET volumes/{id}"| HttpClient
    HttpClient -->|"HTTPS + API key"| GoogleAPI

    %% BookService ↔ DB
    BookService -->|"query · add · commit · delete"| DBEngine
    DBEngine -->|"SQL"| SQLite

    %% DB ↔ domain
    DBEngine -.->|"mapea ORM"| BookModel
    Schemas -.->|"serializa/valida"| BookService
    BookService -.->|"BookRead response"| APIRouter
    BookService -.->|"dict a template"| WebRouter

    %% Estilo
    classDef capa fill:#e8f4fd,stroke:#1f6feb,color:#0b3d91
    classDef externo fill:#fff4e1,stroke:#d97706,color:#7c2d12
    classDef cliente fill:#f0fdf4,stroke:#16a34a,color:#14532d
    class INTERFACES,APPLICATION,INFRASTRUCTURE,DOMAIN capa
    class GoogleAPI,SQLite externo
    class CLIENTS cliente
```

## Reglas de dependencia

- Las flechas sólidas (**→**) indican **llamadas reales** (HTTP, SQL, función).
- Las flechas punteadas (**-.->**) indican **mapeo o transformación** (ORM, Pydantic).
- Una capa **nunca** importa de una capa superior. `domain` no conoce FastAPI ni SQLAlchemy
  directo (lo hace a través de la sesión inyectada). `application` no conoce HTTP ni
  templates. `infrastructure` no conoce routers.

## Puntos clave para la evaluación

| Punto | Dónde se ve |
|---|---|
| Separación de responsabilidades | 4 subgrafos sin ciclos |
| Inyección de dependencias | `Depends(get_db)` + `Depends(get_book_service)` |
| Aislamiento del cliente externo | `HttpClient` con reintentos envuelve a `GoogleBooksClient` |
| Persistencia reemplazable | Cambiar `DATABASE_URL` migra de SQLite a Postgres sin tocar `BookService` |
| Doble interfaz sobre la misma lógica | UI y REST llaman al **mismo** `BookService` |
