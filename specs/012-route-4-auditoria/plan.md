# Plan 012 — Ruta 4 completa: Auditor interno PIMS (Fase F11)

**Estado:** en ejecución.

## Diseño de los 10 módulos (`content/routes/4-auditor/`)

| Orden | Slug | Min | Tipo ejercicio | Ejemplo resuelto | Enfoque de auditoría |
|---|---|---:|---|---|---|
| 1 | `01-principios-de-auditoria` | 150 | `branching` | `01-principios-de-auditoria.reference.md` | Imparcialidad, independencia (`OTI`/`DPO`/`ORA`), confidencialidad, enfoque basado en evidencia |
| 2 | `02-programa-de-auditoria` | 180 | `document_form` | `02-programa-de-auditoria.reference.md` | Programa anual (`Apéndice 1`): cobertura 6 oficinas UNSA, priorización por riesgos, calendario < Revisión |
| 3 | `03-plan-y-criterios` | 200 | `document_form` | `03-plan-y-criterios.reference.md` | Plan de auditoría a `OBU` (`disjoint` con dueño, insumos, métodos, agenda) |
| 4 | `04-listas-de-verificacion` | 200 | `audit_checklist` (`generator: audit_checklist_from_pims`) | `04-listas-de-verificacion.reference.md` | Pregunta + evidencia objetiva + veredicto desde `pims_requirements` y BD viva |
| 5 | `05-entrevistas-y-evidencia` | 200 | `branching` | `05-entrevistas-y-evidencia.reference.md` | Preguntas abiertas, muestreo representativo (no sesgado) y triangulación |
| 6 | `06-simulacion-auditar-el-pims` | 240 | `matching` (`pims_audit_findings`, preservado) | `06-simulacion-auditar-el-pims.reference.md` | Clasificación real sobre los 11 requisitos PIMS en BD |
| 7 | `07-hallazgos-y-no-conformidades` | 200 | `nonconformity_form` | `reference_doc: pims-no-conformidades` | Corrección vs. causa raíz vs. acción correctiva + verificación tras lag en brechas PIMS |
| 8 | `08-informe-y-seguimiento` | 200 | `document_form` | `08-informe-y-seguimiento.reference.md` | `Apéndice 2`: `count_matches` (`nc_count` ↔ detalle), fecha post-auditoría y criterio+evidencia+fallo |
| 9 | `09-competencia-del-auditor` | 150 | `competence_matrix` | `09-competencia-del-auditor.reference.md` | Competencia ISO 19011, formación R4, evaluación supervisada e independencia |
| 10 | `10-evaluacion-de-la-ruta` | 200 | `quiz` (`final: true`) | `10-evaluacion-de-la-ruta.reference.md` | Examen final de Auditor Interno (10 casos UNSA) |

Total: `150 + 180 + 200 + 200 + 200 + 240 + 200 + 200 + 150 + 200 = 1920` min (`32 h`). Total plataforma: `84 h`.

## Actualización de tests existentes que asumían módulos `planned`
- `tests/unit/test_routes_2_4_content.py`: todas las rutas (R1..R4) tienen 0 módulos `planned` y 100 % ejercitación válida (`solve()` = 100); `test_soa_and_planned.py` continúa probando la mecánica `planned` con fixtures propios sintéticos.
- `tests/integration/test_routes_chain_api.py`: `("auditor", 10, 0)`, `total_hours_credited == 84.0`; además, la prueba de `409 module_planned` inserta un módulo `planned` temporal sintético o valida mediante repositorio/BD sin depender de contenido sin terminar en producción!
- `tests/integration/test_analytics_api.py`: verificar las 4 rutas completas (0 `planned`), actualizar expectativa de `auditor` (`len(modules) == 10`).
- `frontend/e2e/document-practice.spec.ts`: añadir verificación E2E + `axe-core` de R4 (`audit_checklist` dinámico y `document_form` Informe de auditoría).
