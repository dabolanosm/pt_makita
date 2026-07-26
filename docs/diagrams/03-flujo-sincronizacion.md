# Diagrama 3 — Flujo de sincronización (`POST /api/sync`)

**Niveles cubiertos:** 3 (Consumo de API externa) · 4 (Procesamiento y almacenamiento) · 6 (Integración)

Este diagrama de flujo describe el camino completo que recorre una petición
`POST /api/sync` desde que el cliente envía la consulta hasta que los libros quedan
persistidos en SQLite, incluyendo los caminos de caché, reintento, dedup, error y
validación.

```mermaid
flowchart TD
    Start(["📥 POST /api/sync<br/>body: {query, max_results}"]) --> Validate1{"¿max_results ≤ 10?"}
    Validate1 -->|No| Err400["❌ ValidationError 422<br/>'max_results must be 10 or less'"]
    Validate1 -->|Sí| CacheCheck{"¿query en<br/>_query_cache<br/>y TTL válido?"}

    CacheCheck -->|Sí · HIT| UseCache["📦 Reutilizar items<br/>del caché (60s TTL)"]
    CacheCheck -->|No · MISS| CallGB["🌐 GET volumes?q=&maxResults=<br/>Google Books API"]

    CallGB --> HTTPGet["HttpClient.get<br/>async con reintentos"]
    HTTPGet --> NetOK{"¿Respuesta<br/>válida?"}
    NetOK -->|5xx / 429| RetryCheck{"intento < 3?"}
    RetryCheck -->|Sí| Backoff["⏱️ sleep 1s/2s/4s + jitter<br/>(0–0.5s aleatorio)"]
    Backoff --> HTTPGet
    RetryCheck -->|No| Err502["❌ ExternalAPIError 502<br/>'Rate limit or server error'"]
    NetOK -->|4xx| ErrClient["❌ ExternalAPIError 4xx<br/>'Google Books API client error'"]
    NetOK -->|RequestError| ErrNet["❌ ExternalAPIError 502<br/>'Network error contacting Google Books'"]
    NetOK -->|2xx| ParseResp["Parsear response.json()<br/>extraer items[]"]

    UseCache --> Dedup
    ParseResp --> Dedup["🧹 Dedup en memoria<br/>set de google_id"]

    Dedup --> LoopStart{"Para cada item"}
    LoopStart -->|siguiente| HasID{"¿tiene<br/>google_id?"}
    HasID -->|No| Skip["⏭️ skip"]
    HasID -->|Sí| AlreadySeen{"¿google_id ya<br/>visto en este batch?"}
    AlreadySeen -->|Sí| Skip
    AlreadySeen -->|No| ParseVolume["_parse_volume_info()<br/>· title<br/>· authors (json)<br/>· categories (json)<br/>· thumbnail_url, etc."]

    ParseVolume --> DBLookup["🔍 SELECT books<br/>WHERE google_id = ?"]
    DBLookup --> Exists{"¿Existe?"}
    Exists -->|No| Insert["➕ INSERT new Book<br/>db.flush()<br/>new_count++"]
    Exists -->|Sí| Update["✏️ UPDATE campos<br/>+ updated_at<br/>updated_count++"]

    Insert --> LoopStart
    Update --> LoopStart
    Skip --> LoopStart

    LoopStart -->|fin del batch| Commit["💾 db.commit()"]
    Commit --> CacheStore["📦 _set_in_cache(query, items)"]
    CacheStore --> LogOK["📝 log info:<br/>query · results · new · updated · elapsed_ms"]
    LogOK --> Respond(["✅ 200 OK<br/>list[BookRead]"])

    %% Estilo
    classDef ok fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef err fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    classDef cache fill:#fef9c3,stroke:#ca8a04,color:#713f12
    classDef ext fill:#dbeafe,stroke:#1d4ed8,color:#1e3a8a

    class Respond,Commit,Insert,Update,LogOK ok
    class Err400,Err502,ErrClient,ErrNet err
    class CacheCheck,UseCache,CacheStore cache
    class CallGB,HTTPGet,NetOK,RetryCheck,Backoff ext
```

## Reglas de negocio implementadas en el flujo

1. **Validación de entrada** — `max_results` está limitado a 10 en el `Pydantic Field`
   (`sync.py`) **y** se vuelve a verificar en `BookService.sync_from_query()` por
   seguridad. Es un cinturón + tirantes.
2. **Caché de consultas** — Implementado como `dict[str, tuple[list, float]]` en memoria
   del proceso. TTL de **60 s**. La clave es la query normalizada (lower + strip). No
   sobrevive reinicios. No es compartido entre réplicas.
3. **Reintentos con backoff exponencial y jitter** — Manejado en `HttpClient.get()`:
   hasta 3 intentos, delays `[1s, 2s, 4s]` con jitter `[0, 0.5s]`. Solo reintenta
   códigos `429, 500, 502, 503, 504`. Errores 4xx se devuelven al cliente de inmediato.
4. **Deduplicación en dos niveles**:
   - En memoria: `set` de `google_id` para no procesar el mismo libro dos veces en el
     mismo batch.
   - En DB: query `WHERE google_id = ?` para decidir INSERT vs UPDATE.
5. **Manejo de errores transaccionales** — Si algo falla a mitad del batch, `db.rollback()`
   en el `except`. No quedan filas inconsistentes.
6. **Auditoría por log** — `logger.info()` al final con métricas: query, results,
   new, updated, elapsed_ms. No hay tabla de auditoría persistente (mejora futura).
7. **`updated_at` automático** — SQLAlchemy `onupdate=datetime.utcnow` se dispara en
   cada UPDATE.

## Endpoints relacionados (mismo flujo, variaciones menores)

| Endpoint | Variación respecto al flujo |
|---|---|
| `POST /api/sync/seed?confirm=true` | Itera sobre 6 queries semilla en serie. Si una falla, aborta y devuelve 502 con el query que falló. |
| `POST /web/sync` (UI) | Mismo flujo, pero redirige con `?message=...` o `?error=...` en lugar de JSON. |
| `POST /web/books/add` | Variante "un solo libro": `get_by_id(google_id)` + INSERT con dedup. No usa caché. |
| `POST /web/search/google` | No persiste: solo llama a `search_books()` y muestra resultados en la UI. |
