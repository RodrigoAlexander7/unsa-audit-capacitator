# Tasks 006 — Rutas 2–4 y evaluación controller/processor

- [x] T1 Contrato `contracts/openapi.yaml` (AC-006-14)
- [x] T2 learning: `planned` (dominio, loader, repo, API) + tests (AC-006-1, 2)
- [x] T3 learning: `soa_form` (validate/public/grade) + tests (AC-006-5)
- [x] T4 learning: `pims_audit_findings` + `LearningFacts` + tests (AC-006-7)
- [x] T5 Contenido R2–R4 (estructura + 3 demos) (AC-006-1, 4, 6)
- [x] T6 assessment: dominio, aplicación, infraestructura, migración 0006 (AC-006-9..13)
- [x] T7 assessment: interface + wiring + bancos de preguntas (AC-006-9, 10, 11, 12)
- [x] T8 tests de integración (cadena R1→R4, gating, planned, assessments, contrato) (AC-006-3, 8, 10..14)
- [x] T9 Frontend: rutas 2–4, `SoaForm`, `/assessment` (AC-006-16)
- [x] T10 Verificación completa, docs y commit único de la fase (AC-006-15)

## Notas de cierre
- Verificado: ruff, pyright, `alembic check`, **249 tests backend** (173 unit + 76 integración con Postgres real), svelte-check, 18 vitest y build.
- La cadena R1→R2→R3→R4 se recorre de punta a punta por la API (`test_cadena_completa_de_las_cuatro_rutas_acredita_21_horas`): prerrequisitos, `planned` y 21 h (12 + 2 + 3 + 4).
- El demo de auditoría se comprueba contra el estado **real** del PIMS: al publicar el borrador de la SoA (UPDATE en la BD de test) cambia el hallazgo esperado y la respuesta antigua baja a 91 %.
- La UI de `SoaForm` y de `/assessment` se valida con tests de lógica (`completion/canSubmit`, svelte-check) y de API; el recorrido visual completo se hace en el smoke E2E de la Fase 7.
- Decisión: cada ruta 2–4 desarrolla un único módulo obligatorio (el demo) y los demás figuran como «Próximamente» (`planned`). Las horas acreditadas son las del módulo demo y la UI lo avisa.
- Decisión: la evaluación es *crear + enviar una vez* (sustituye `answers`/`finish` del PLAN §9); el intento guarda el resultado calculado con las etiquetas de cláusula del momento.
- Pendiente: analytics y panel del superadmin (F6) usarán `assessments.result` (competencias y requisitos).
