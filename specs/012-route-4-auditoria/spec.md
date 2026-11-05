# Spec 012 — Ruta 4 completa: Auditor interno PIMS (32 h, Fase F11)

**Estado:** en ejecución (aprobado dentro del plan F8–F13).

## Objetivo
Completar los **10 módulos** de la Ruta 4 (`auditor`, 1920 minutos = 32 horas), retirando `planned: true` de `01..05` y `07..10`, conservando intacto el módulo demo `06-simulacion-auditar-el-pims` (`pims_audit_findings`), e incorporando lección práctica, ejemplo resuelto y ejercicio determinista ISO 19011 + ISO/IEC 27701 en cada módulo para totalizar **84 horas** curriculares en toda la plataforma.

## Criterios de aceptación (AC-012)
- **AC-012-1 (Completitud y 32 h de R4 — 84 h totales):** La ruta `auditor` tiene 10 módulos publicados (`planned: false`, `mandatory: true`), órdenes `1..10`, módulo 10 `is_final = True` y suma exacta de `1920` minutos (`32 h`), alcanzando `84 h` (`12 + 16 + 24 + 32`) en toda la cadena.
- **AC-012-2 (Preservación de R4 Módulo 06):** `06-simulacion-auditar-el-pims` mantiene intacto su generador dinámico `pims_audit_findings` (`AC-006-7`), añadiendo únicamente guía resuelta de referencia lado a lado.
- **AC-012-3 (Principios, Entrevistas y Competencia del Auditor):** `01-principios-de-auditoria` (`branching`), `05-entrevistas-y-evidencia` (`branching`) y `09-competencia-del-auditor` (`competence_matrix`) enseñan imparcialidad (no auditar el trabajo propio), muestreo significativo, triangulación de evidencias y segregación evaluadora.
- **AC-012-4 (Programa Anual y Plan Individual de Auditoría — `document_form`):** `02-programa-de-auditoria` planifica las 6 oficinas UNSA con priorización basada en riesgos, métodos combinados, equipo imparcial (`disjoint`) y secuencia previa a Revisión por Dirección (`date_order`); `03-plan-y-criterios` delimita criterios, insumos e independencia frente al área auditada (`OBU`).
- **AC-012-5 (Lista de Verificación Dinámica — `audit_checklist_from_pims`):** `04-listas-de-verificacion` usa `kind: "audit_checklist"` con `generator: "audit_checklist_from_pims"` enlazando `pims_requirements.clause_ref` y el estado real en BD para seleccionar pregunta, evidencia y veredicto.
- **AC-012-6 (No Conformidades e Informe con Consistencia Matemática):** `07-hallazgos-y-no-conformidades` usa `nonconformity_form` con `reference_doc: pims-no-conformidades`; `08-informe-y-seguimiento` valida mediante `document_form` la regla `count_matches` (`nc_count` == líneas de NC detalladas sin contar observaciones), `date_order` posterior al cierre de campo y redacción objetiva (criterio + evidencia + incumplimiento).
- **AC-012-7 (Evaluación Final y Efectos Colaterales):** `10-evaluacion-de-la-ruta` cierra R4 con `quiz` de 10 casos ISO 19011/27701 (`final: true`). `seed/solutions.py`, `seed/demo.py` (`ana.quispe` en R4), `test_routes_2_4_content.py`, `test_routes_chain_api.py` (`84.0 h`), `test_analytics_api.py`, `docs/demo.md` y Playwright E2E + `axe-core` reflejan todas las rutas sin módulos `planned` (`0`).
- **AC-012-8 (Calidad y Restricciones):** Cumple `make verify` completo y 0 copia literal desde `raw/`.
