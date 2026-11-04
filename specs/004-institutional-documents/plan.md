# Plan 004 — Documentos institucionales versionados

## Módulo `documents`
**domain**
- `documents.py`: `DocumentKind`, `ChangeImpact`, `ChangeStatus`, `Document`, `DocumentVersion`, `ChangeRequest`.
- `diff.py`: `normalize_content`, `content_hash` (SHA-256), `compute_diff` (hunks con contexto de 3 líneas, vía `difflib.SequenceMatcher.get_grouped_opcodes`) → `Diff(hunks, additions, deletions)`.

**application**
- `ports.py`: `DocumentRepository`, `DocumentSource` (+ vistas `DocumentSummary`, `ChangeRequestView`).
- `errors.py`: `DocumentNotFound`, `VersionNotFound`, `ChangeRequestNotFound`, `InvalidChangeRequest`, `NoChanges`, `AlreadyResolved`, `StaleBase`.
- `use_cases.py`: `ListDocuments`, `GetDocument`, `ListVersions`, `GetVersion`, `GetDiff`, `ProposeChange`, `ListChangeRequests`, `GetChangeRequest`, `ResolveChangeRequest`, `SyncDocuments`.

**infrastructure**
- `models.py` (ORM), `sqlalchemy_repository.py`, `content_loader.py` (lee `content/institutional/<codigo>/`).

**interface**: `router.py`; `ResolveChangeRequest` solo con `SuperAdmin` (dependencia de identity).

## Decisiones
- **Atomicidad y concurrencia:** `apply_change` hace en una transacción: `UPDATE documents SET current_version_id=:new WHERE id=:id AND current_version_id=:base` (compare-and-set); si no afecta filas → `StaleBase` y se hace rollback. `UNIQUE(document_id, number)` protege la numeración.
- **Solicitud = propuesta de texto completo** (no parche): el diff se calcula contra la versión base. Simple y robusto para un POC.
- **Impacto** (`cosmetico|procedimental|estructural`) conecta con lo practicado en el módulo 5 de la Ruta 1 y servirá a analytics.
- **Autor:** `author_id` (nullable para importaciones) + `author_label` (nombre congelado al crear la versión).
- **Unidad responsable:** `owner_unit_code` (texto) resuelto a nombre con un join de lectura a `org_units`; sin FK para no acoplar el seed.
- **Seed:** inserta lo que falta y no pisa lo existente; `--reset-documents` borra y recarga documentos, versiones y solicitudes. Ids deterministas (`uuid5`).
- **Contenido:** `content/institutional/<codigo>/document.yaml` + `vN.md` (frontmatter `message`, `author`, `date`). La vigente es la mayor `N`.
- **Tipos** como cadena validada contra un conjunto cerrado (la Fase 4 lo amplía con `PIMS_*`).

## Datos (migración 0004)
`documents`, `document_versions` (UNIQUE document_id+number), `change_requests`.

## Frontend
`/documents` (lista + solicitudes abiertas), `/documents/[code]` (contenido, historial, solicitudes), `/documents/[code]/diff`, `/documents/[code]/propose`, `/documents/[code]/changes/[id]` (detalle + resolver si superadmin). Componente `DiffView` y `DiffText` (este último reutilizado en los ejercicios del módulo 5).

## Tests
- Unit: normalización/hash/diff, casos de uso con repositorio en memoria (permisos a nivel de caso de uso no aplican: el rol se verifica en interface), validez del contenido y su cadena de versiones.
- Integración (Postgres real): flujo propuesta → aprobación → versión nueva con diff; stale_base; rechazo; permisos 401/403; seed idempotente y `reset`; contrato.
