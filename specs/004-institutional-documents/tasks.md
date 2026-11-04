# Tasks 004 — Documentos institucionales versionados

- [x] T1 Contrato `contracts/openapi.yaml` (AC-004-15)
- [x] T2 domain: entidades, normalización, hash, diff + unit tests (AC-004-4, 12, 6)
- [x] T3 application: puertos, errores, casos de uso + unit tests con fakes (AC-004-5..11)
- [x] T4 infrastructure: ORM, repositorio (compare-and-set), content loader (AC-004-9, 10, 13, 14)
- [x] T5 migración 0004 (autogenerate + FK circular `documents ↔ document_versions` creada con `ALTER`; probada subir/bajar/subir y `alembic check` sin diferencias)
- [x] T6 Contenido: 5 documentos con historial en `content/institutional/` (AC-004-13)
- [x] T7 interface: router, schemas, permisos, wiring en `main.py` (AC-004-1..11)
- [x] T8 seed: `SyncDocuments` + `--reset-documents` (AC-004-14)
- [x] T9 tests de integración (flujo completo, permisos, stale, concurrencia, seed, contrato) (AC-004-1..15)
- [x] T10 Frontend: lista, detalle, historial, diff, propuesta, revisión; `DiffView`/`DiffText` y módulo 5 (AC-004-17)
- [x] T11 Verificación completa, docs (README/C4/PLAN) y commit único de la fase (AC-004-16)

## Notas de cierre
- Verificado: ruff, pyright, **166 tests backend** (109 unit + 57 integración con Postgres real, incluida una prueba con 4 aprobaciones simultáneas de la misma solicitud: gana una sola), svelte-check, **17 vitest** y build.
- AC-004-17 verificado en el navegador integrado: lista de documentos, diff con signos `+`/`−` y numeración, propuesta (editar texto, justificación, impacto), aprobación como superadmin → v3 con trazabilidad y enlace al diff. Como participante (SSR + API): sin formulario de resolver, la API responde 403 y la solicitud abierta muestra "espera la decisión del superadmin". El módulo 5 de la Ruta 1 muestra sus diffs con el nuevo estilo (4 líneas añadidas, 3 eliminadas).
- Se encontró y corrigió un bug en la UI: los selectores del diff no reflejaban `from`/`to` (se usa `selected` por opción).
- **Seguridad:** el Markdown de documentos y lecciones se renderiza con `lib/markdown.ts`, que escapa el HTML crudo, descarta imágenes remotas y enlaces `javascript:`/`data:` (4 tests). Los documentos pueden contener texto propuesto por usuarios, aunque solo se muestra tras aprobación.
- `normalize_content` también quita líneas en blanco al inicio/fin (detectado por un test de contenido real).
- **Hallazgo sembrado a propósito:** el Cuadro de Asignación de Personal (27 plazas) no incluye el cargo de Oficial de Protección de Datos creado en el MOF v2 y el ROF v3. Sirve de caso para los ejercicios de auditoría de la Ruta 4 (documentos incoherentes entre sí).
- Pendiente para fases siguientes: plantillas PIMS (F4), ejercicio de revisión de diffs basado en el historial real (F5), analytics de solicitudes (F6).
