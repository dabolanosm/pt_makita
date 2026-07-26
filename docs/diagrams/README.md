# Diagramas — Book Library Sync

Este directorio contiene los diagramas de arquitectura, datos, flujo y despliegue de
**Book Library Sync**. Todos están escritos en [Mermaid](https://mermaid.js.org/), que
se renderiza automáticamente en GitHub, GitLab, VS Code y la mayoría de wikis técnicas.

## Índice

| # | Diagrama | Archivo | Niveles cubiertos |
|---|---|---|---|
| 1 | Arquitectura general (4 capas + componentes externos) | [`01-arquitectura-general.md`](01-arquitectura-general.md) | 1 · 2 · 5 · 6 |
| 2 | Modelo de datos (ER de la tabla `books`) | [`02-modelo-datos.md`](02-modelo-datos.md) | 4 |
| 3 | Flujo de sincronización (`POST /api/sync`) | [`03-flujo-sincronizacion.md`](03-flujo-sincronizacion.md) | 3 · 4 · 6 |
| 4 | Secuencia UML del sync + variantes | [`04-secuencia-sync.md`](04-secuencia-sync.md) | 3 · 6 |
| 5 | Despliegue: local vs Render vs futuro | [`05-despliegue.md`](05-despliegue.md) | 1 · 7 |

## Cómo leerlos

- **Empieza por el 1** si quieres entender la estructura completa del proyecto.
- **Salta al 2** si lo que te interesa es el modelo de datos.
- **El 3 y el 4 cuentan lo mismo de dos formas** — el 3 es para entender la lógica de
  negocio, el 4 para entender el orden temporal de las llamadas. Si solo vas a leer
  uno, lee el 4 (es más preciso y muestra todos los actores).
- **El 5** es relevante si te importa cómo corre en local o en producción.

## Cómo regenerarlos / exportarlos a PNG

Los diagramas son texto plano. Para exportarlos a imagen (por ejemplo, para incluirlos
en un PDF o en una presentación):

```bash
# Opción 1: con npx (no requiere instalar nada global)
npx -p @mermaid-js/mermaid-cli mmdc -i docs/diagrams/01-arquitectura-general.md -o out/01.png

# Opción 2: edición live en el navegador
# Abre https://mermaid.live y pega el contenido del bloque ```mermaid
```

## Por qué Mermaid y no PNG/SVG

- ✅ Texto plano → se commitea sin generar diffs de binarios.
- ✅ Se renderiza nativo en GitHub (en `code review` y en el `README`).
- ✅ Cualquiera puede editarlo sin abrir Figma, draw.io ni Visio.
- ✅ Versionado: los `git blame` muestran exactamente cuándo cambió qué relación.
- ❌ Limitación: Mermaid no hace diagramas muy artísticos (ni debe). Para eso, exportar
  a PNG y editar en Figma.

## Cobertura contra la rúbrica de la prueba

| Criterio de evaluación (Prueba Técnica §5) | Diagrama que lo cubre |
|---|---|
| Arquitectura clara | #1 |
| Separación de capas | #1 |
| Modelo de datos bien diseñado | #2 |
| Estrategia de almacenamiento | #2, #3 |
| Manejo de errores y reintentos | #3, #4 |
| Sincronización e idempotencia | #3, #4 |
| Uso de Docker | #5 |
| Despliegue documentado | #5 |
| Calidad de la documentación | Este índice + cada diagrama |
