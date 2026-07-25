# Guía de despliegue (Nivel 7)

Esta guía documenta cómo publicar **Book Library Sync** en una URL pública con HTTPS, sin modificar el código fuente. Se utiliza [Render.com](https://render.com) como plataforma de despliegue porque:

- Tiene plan gratuito funcional.
- Lee el `Dockerfile` directamente, sin requerir adaptadores.
- Genera HTTPS automático.
- Despliega con un solo click desde GitHub.

---

## 1. Requisitos previos

- Repositorio público (o privado con acceso para Render) en GitHub con este código.
- API key de Google Books (ver `README.md` para cómo obtenerla).
- Una cuenta en [render.com](https://render.com) (gratis, puedes entrar con GitHub).

## 2. Despliegue con Blueprint (1 click)

Este repo incluye un archivo `render.yaml` (Render Blueprint) que define toda la infraestructura. Render lo lee automáticamente al conectar el repo.

### Paso a paso

1. Entra a https://dashboard.render.com/select-repo?type=blueprint.
2. Selecciona el repo `dabolanosm/pt_makita` (o como lo hayas nombrado).
3. Render detecta el `render.yaml` y muestra un resumen del servicio a crear.
4. Click en **Apply**.
5. En la pantalla del servicio creado, ve a **Environment** y configura:
   - `GOOGLE_BOOKS_API_KEY` = tu API key real (sin restricción a "Books API" da 403, ver README principal).
6. Render empieza a construir la imagen Docker automáticamente. Tarda 3-5 minutos la primera vez.
7. Cuando el estado pase a **Live**, tu URL pública es algo como:

   ```
   https://book-library-sync.onrender.com
   ```

8. Abre esa URL en el navegador. Verás el dashboard de la app.

### Qué hace el `render.yaml`

```yaml
dockerCommand: "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
```

Este es el único cambio funcional respecto al `Dockerfile` original: **quita el flag `--reload`** (que es para desarrollo) y usa `$PORT`, que es la variable de entorno que Render inyecta automáticamente (suele ser `10000`). El resto del `Dockerfile` queda intacto.

## 3. Verificación post-deploy

Una vez en línea, prueba:

| URL | Esperado |
|---|---|
| `https://<tu-app>.onrender.com/` | Dashboard con la biblioteca (vacía al inicio) |
| `https://<tu-app>.onrender.com/docs` | Swagger UI con todos los endpoints |
| `https://<tu-app>.onrender.com/health` | `{"status":"ok"}` |
| `https://<tu-app>.onrender.com/health/db` | `{"status":"ok","database":"connected"}` |
| `https://<tu-app>.onrender.com/api/books` | `[]` (lista vacía) |

Si todo responde, ve al dashboard y prueba una sincronización con la búsqueda "Programación Python".

## 4. Limitaciones del plan gratuito

- **Cold start:** si la app no recibe tráfico durante 15 minutos, Render la "duerme". El siguiente request tarda 30-50 segundos extra en arrancar. Esto es normal y no es un error.
- **Ephemeral filesystem:** el archivo SQLite (`/app/data/app.db`) **se borra** cada vez que la app se reinicia o se redespliega. Es decir, los libros que sincronices se pierden al redeploy.
- **750 horas/mes de runtime** (suficiente para demo).
- **Sin dominio personalizado** (solo `*.onrender.com`).

## 5. Si quieres datos persistentes

Tienes dos opciones (ninguna requiere tocar el código fuente):

### Opción A — Persistent Disk de Render (1 USD/mes)

Añade esto al `render.yaml`:

```yaml
    disk:
      name: book-data
      mountPath: /app/data
      sizeGB: 1
```

Y cambia el plan de `free` a `starter` (7 USD/mes). Los libros persisten entre redespliegues.

### Opción B — PostgreSQL gratuito externo

1. Crea una DB gratis en [neon.tech](https://neon.tech) o [supabase.com](https://supabase.com).
2. Cambia `DATABASE_URL` en Render a la URL de Postgres que te den.
3. Instala `psycopg2-binary` en `requirements.txt` (un cambio de una línea, no es lógica de negocio).
4. El driver de SQLAlchemy detecta Postgres automáticamente.

> **Nota:** esta opción sí requiere un cambio mínimo en `requirements.txt`. Si prefieres mantener el código 100% intacto, usa la Opción A.

## 6. Alternativas a Render

Si prefieres otra plataforma, el mismo `Dockerfile` funciona sin cambios en:

- **Railway.app:** `https://railway.app/new` → "Deploy from Docker Hub" o conecta el repo. Crea un servicio, detecta el Dockerfile. Tier gratuito: 5 USD/mes de crédito.
- **Fly.io:** `fly launch` en la raíz del proyecto detecta el Dockerfile y configura todo. Tier gratuito generoso.
- **Google Cloud Run:** `gcloud run deploy --source .` desde la raíz. Serverless, escala a cero.

## 7. Troubleshooting

| Síntoma | Causa | Solución |
|---|---|---|
| `403 API_KEY_SERVICE_BLOCKED` al primer sync | API key de Google sin restringir a "Books API" | Restringir en Google Cloud Console (ver README) |
| `503 backendFailed` intermitente | Rate limit de Google Books (~3 req/seg) o geolocalización | Esperar 1-2 min, reintentar. La app ya tiene backoff con jitter |
| App tarda 40s en responder la primera vez | Cold start de Render free tier | Normal, es por el plan gratuito |
| Libros desaparecen tras redeploy | SQLite en filesystem efímero | Ver sección 5 para persistencia |
| Build falla con "permission denied" en `data/` | El directorio `data/` está vacío en el repo | Crear `data/.gitkeep` (ya existe) |

## 8. CI/CD

Render redesplega automáticamente en cada `git push` a la rama principal gracias a `autoDeploy: true`. Para desactivarlo, quita esa línea del `render.yaml` o desmarca "Auto-Deploy" en el dashboard.
