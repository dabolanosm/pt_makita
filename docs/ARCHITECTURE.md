# Arquitectura

Esta aplicación usa un diseño de cuatro capas:

- `domain`: modelos y esquemas de dominio (`Book`, `BookCreate`, `BookRead`).
- `infrastructure`: acceso a servicios externos y a la base de datos (`HttpClient`, `GoogleBooksClient`, SQLAlchemy `engine`, `get_db`).
- `application`: lógica de negocio y orquestación (`BookService`).
- `interfaces`: endpoints HTTP para API REST y la UI web, incluyendo la capa de templates Jinja2 y la lógica de interacción del frontend ligero.

## Diagramas

Los diagramas detallados están en [`docs/diagrams/`](diagrams/README.md). Resumen rápido:

| # | Diagrama | Cubre |
|---|---|---|
| 1 | Arquitectura general (4 capas + componentes externos) | Niveles 1, 2, 5, 6 |
| 2 | Modelo de datos (ER de la tabla `books`) | Nivel 4 |
| 3 | Flujo de sincronización (`POST /api/sync`) | Niveles 3, 4, 6 |
| 4 | Secuencia UML del sync + variantes | Niveles 3, 6 |
| 5 | Despliegue: local vs Render vs futuro | Niveles 1, 7 |

Diagrama simple (ASCII, solo para tener una vista rápida en el README):

```
[browser] --> [FastAPI web router] --> [BookService] --> [SQLite DB]
                           |
                           --> [Google Books API]
```
