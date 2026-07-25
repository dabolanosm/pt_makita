# Arquitectura

Esta aplicación usa un diseño de cuatro capas:

- `domain`: modelos y esquemas de dominio (`Book`, `BookCreate`, `BookRead`).
- `infrastructure`: acceso a servicios externos y a la base de datos (`HttpClient`, `GoogleBooksClient`, SQLAlchemy `engine`, `get_db`).
- `application`: lógica de negocio y orquestación (`BookService`).
- `interfaces`: endpoints HTTP para API REST y la UI web.

Diagrama simple:

```
[browser] --> [FastAPI web router] --> [BookService] --> [SQLite DB]
                           |
                           --> [Google Books API]
```
