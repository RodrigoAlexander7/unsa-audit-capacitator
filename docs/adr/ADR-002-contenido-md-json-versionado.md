# ADR-002 — Contenido en MD/JSON versionado en el repo

- **Estado:** aceptada
- **Fecha:** 2026-11-11

## Contexto
Hay mucho contenido (rutas, ejercicios, plantillas institucionales y del PIMS) con información UNSA **ficticia**. Debe ser revisable, diffable y regenerable.

## Decisión
- Fuente de verdad en `content/` (Markdown con frontmatter + JSON para ejercicios).
- Al arrancar/seed, el backend sincroniza `content/` a PostgreSQL como versión inicial.
- Las modificaciones posteriores a documentos institucionales se hacen en la app con *change requests* y quedan como versiones en BD (modelo "git de incidencias").
- El contenido ISO es **parafraseado**; las cláusulas se guardan como datos (`clause_ref`), no hardcodeadas.

## Consecuencias
+ Contenido revisable por PR; seed reproducible.
− Dos fuentes (repo y BD) tras editar en la app; se mitiga con exportación a MD si hace falta.
