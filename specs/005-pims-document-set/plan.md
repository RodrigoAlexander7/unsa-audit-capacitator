# Plan 005 — Conjunto documental del PIMS

Se amplía el módulo `documents` (no se crea otro módulo: los documentos PIMS son documentos).

## Dominio
- `DocumentKind` += 11 tipos `PIMS_*` (`PIMS_SCOPE`, `PIMS_PRIVACY_POLICY`, `PIMS_RISK_PROCESS`, `PIMS_SOA`, `PIMS_TREATMENT_PLAN`, `PIMS_SECURITY_PROGRAM`, `PIMS_RISK_RESULTS`, `PIMS_TREATMENT_RESULTS`, `PIMS_COMPETENCE`, `PIMS_MONITORING`, `PIMS_NONCONFORMITIES`).
- `DocumentLifecycle(in_force | draft)`; `Document` gana `lifecycle` (default `in_force`) y `review_date` (default `None`).
- `pims.py`: `PimsRequirement`, `RequirementState`, `evaluate_state(...)` (pura, precedencia + issues), `PimsStatus`, `Completeness`.

## Aplicación
- Puertos: `PimsRequirementRepository` (`replace_all`, `list_all`) y `PimsRequirementSource`.
- Casos de uso: `ListPimsRequirements`, `GetPimsCompleteness(clock)`, `SyncPimsRequirements`.
- `SyncDocuments` no cambia (ya no pisa lo existente).

## Infraestructura
- Migración 0005: `documents.lifecycle` (default `in_force`), `documents.review_date`; tabla `pims_requirements` (`code` único, `document_kind` único, `sort_order`).
- `content/pims/requirements.yaml` → `FilePimsRequirementSource`; el loader de documentos lee `lifecycle` y `review_date`.
- Seed: `sync_pims_requirements` (reemplazo total, es dato de referencia) antes de `sync_documents`.

## Interface
`GET /pims/requirements`, `GET /pims/completeness`; `/documents` expone `lifecycle` y `review_date`.

## Contenido (original, sin copiar plantillas)
10 documentos en `content/institutional/pims-*/v1.md` (+ `document.yaml` con `lifecycle`, `review_date`, `owner_unit`), redactados para la UNSA ficticia y ISO 27701: roles controller/processor, categorías sensibles, derechos de los titulares, brechas de datos. Los textos incluyen carencias plausibles (p. ej. la matriz de competencia sin capacitación registrada para el Oficial de Protección de Datos) para la Ruta 4.

## Frontend
`/documents/pims` (resumen + matriz + evidencia esperada); `ChangeBadge`-like `StateBadge`; la lista de documentos muestra `Borrador`/`Vencido`.

## Tests
- Unit: precedencia/issues (parametrizado), completitud con reloj fijo, validez de `requirements.yaml` y de los documentos PIMS, reparto sembrado con `today = 2026-11-11`.
- Integración: `/pims/*`, 401, campos nuevos en `/documents`, propuesta + aprobación sobre un documento PIMS, seed idempotente, contrato.
