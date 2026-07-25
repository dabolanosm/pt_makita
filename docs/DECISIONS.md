# Decisiones técnicas

| Decisión | Alternativas | Por qué |
|---|---|---|
| Usar Google Books API | Open Library, Goodreads | Google Books es fácil de integrar, bien documentada y no requiere OAuth para búsquedas básicas.
| Usar FastAPI | Django, Flask | FastAPI es liviana, rápida y ofrece documentación OpenAPI automática.
| Usar SQLite | PostgreSQL, MySQL | SQLite es suficiente para una prueba técnica local y funciona bien con Docker sin infraestructura adicional.
| Usar Jinja2 para UI | React, Vue | Jinja2 permite una UI sencilla con bajo overhead y sin dependencia de bundlers.
| No implementar CSRF completo | CSRF completo, JWT, tokens | Para esta prueba técnica la protección completa sería extra; se documenta como limitación.
