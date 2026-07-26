# Decisiones técnicas

| Decisión | Alternativas | Por qué |
|---|---|---|
| Usar Google Books API | Open Library, Goodreads | Google Books es fácil de integrar, bien documentada y no requiere OAuth para búsquedas básicas.
| Usar FastAPI | Django, Flask | FastAPI es liviana, rápida y ofrece documentación OpenAPI automática.
| Usar SQLite | PostgreSQL, MySQL | SQLite es suficiente para una prueba técnica local y funciona bien con Docker sin infraestructura adicional.
| Usar Jinja2 para UI | React, Vue | Jinja2 permite una UI sencilla con bajo overhead y sin dependencia de bundlers, adecuada para una prueba técnica y para mantener el foco en la lógica de negocio.
| Diseñar la UI con un sistema visual propio | Framework CSS o componentes externos | Se priorizó un sistema de diseño propio con variables CSS, tema claro/oscuro y componentes reutilizables para mantener la app ligera y fácil de mantener.
| Eliminar el caché de consultas en memoria | Mantener un caché por request | El caché basado en un diccionario del servicio no daba un beneficio real en el wiring actual y se removió para evitar confusión y mantener el comportamiento predecible.
| No implementar CSRF completo | CSRF completo, JWT, tokens | Para esta prueba técnica la protección completa sería extra; se documenta como limitación.
