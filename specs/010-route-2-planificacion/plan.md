# Plan 010 — Ruta 2 completa: Interpretación PIMS (Fase F9)

**Estado:** en ejecución.

## Diseño modular de los 8 módulos (`content/routes/2-interpretacion/`)

| Orden | Slug | Min | Tipo ejercicio | Ejemplo resuelto | Regla clave enseñada |
|---|---|---:|---|---|---|
| 1 | `01-contexto-y-alcance` | 120 | `document_form` | `reference_doc: pims-alcance` | Coherencia unidad↔sistema, aprobación Rector vs. DPO, revisión ≤ 365 d, exclusiones justificadas |
| 2 | `02-liderazgo-y-politica` | 120 | `document_form` | `reference_doc: pims-politica-privacidad` | Autoridad directiva, principios, derechos ARCO, datos sensibles y compromiso de objetivos |
| 3 | `03-riesgos-de-privacidad` | 140 | `risk_table` | `03-riesgos-de-privacidad.reference.md` | Escala `C + P`, umbral `< 3`, consecuencia `2` obligatoria ante datos sensibles |
| 4 | `04-controles-y-aplicabilidad` | 140 | `soa_form` | `04-controles-y-aplicabilidad.reference.md` | Aplicabilidad por rol (`controller`/`processor`) vs. exclusiones inválidas por costo |
| 5 | `05-controller-y-processor` | 120 | `branching` | `05-controller-y-processor.reference.md` | Delimitación UNSA responsable vs. `OTI` operativo vs. proveedores nube/laboratorio |
| 6 | `06-del-requisito-al-documento` | 120 | `matching` (preservado) | `06-del-requisito-al-documento.reference.md` | Mapeo pregunta de auditoría → los 11 requisitos PIMS (método vs. plan vs. resultado) |
| 7 | `07-competencia-monitoreo-mejora` | 100 | `competence_matrix` | `reference_doc: pims-competencia` | Competencia ≠ asistencia; evidencia de eficacia + evaluador independiente |
| 8 | `08-evaluacion-de-la-ruta` | 100 | `quiz` (`final: true`) | `08-evaluacion-de-la-ruta.reference.md` | Examen integrador de 10 ítems situacionales sobre interpretación en UNSA |

Total: `120 + 120 + 140 + 140 + 120 + 120 + 100 + 100 = 960` min (`16 h`).

## Ajustes en pruebas y documentación
1. **Tests unitarios (`tests/unit/test_routes_2_4_content.py`):** validar R2 completa (8 módulos publicados, suma 960 min, módulo 8 final, validación/saneamiento/`solve()` 100 % en todos los ejercicios de R2; conservar R3 y R4 con `planned` hasta F10/F11).
2. **Tests de integración (`test_routes_chain_api.py`, `test_analytics_api.py`):** actualizar expectativas de conteo (`("interpretacion", 8, 0)`), horas (`16.0` en R2, `35.0` total R1–R4), prueba de módulo `planned` 409 sobre `implementacion`, y población de `_populate` completando los 8 módulos de R2.
3. **E2E (`frontend/e2e/document-practice.spec.ts`):** añadir recorrido real verificando que R2 módulo `01-contexto-y-alcance` despliega el panel lado a lado (`pims-alcance`) y su `document_form` con `axe-core` limpio.
4. **Docs (`docs/demo.md`):** reflejar que R2 completa ya es navegable e interactive de principio a fin (16 h).
