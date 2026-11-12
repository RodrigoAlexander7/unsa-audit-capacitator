# Tasks 009 — Motor de práctica documental (F8)

**Estado:** aprobada (Fase F8).

- [x] T1 Inventario estructural de las 16 plantillas en `docs/practica-documental/inventario-plantillas.md` y verificación de no-copia (AC-009-1)
- [x] T2 Contrato OpenAPI `specs/009-document-practice/contracts/openapi.yaml` (AC-009-10, 15)
- [x] T3 `learning/domain`: ampliar `ExerciseKind`, `Module.reference_*`, política `REVEAL_AFTER_ATTEMPTS = 3` y módulo puro `document_exercises.py` con los 6 tipos (`validate_spec`, `to_public`, `grade`, `solution_guide`) (AC-009-2..9)
- [x] T4 Tests unitarios exhaustivos de dominio para los 6 tipos (aciertos 100 %, errores típicos, rúbricas, reglas cruzadas, datos sensibles, umbrales, `to_public` sin filtraciones y 422 `InvalidAnswer`) (AC-009-2..8)
- [x] T5 `learning/application`: enriquecer `UniversitySnapshot`, añadir `count_attempts` en `LearningRepository`, implementar generador `audit_checklist_from_pims` y política de revelación tras 3 intentos en `SubmitAttempt` + tests unitarios con fakes (AC-009-6, 9, 11)
- [x] T6 `learning/infrastructure` + migración `0008_document_practice.py`: columnas `reference_title`/`reference_md`, `count_attempts` SQL, resolución de `reference_doc` / `.reference.md` en `FileContentSource` y facts enriquecidos en `SqlAlchemyUniversityFacts`/`LearningFacts` (AC-009-10, 11, 15)
- [x] T7 `learning/interface` + `seed/solutions.py`: exponer `reference`, `attempt_number`, `solution_revealed` y `solution_guide`, y ampliar `solve`/`wrong` para los 6 tipos (AC-009-9, 10, 12)
- [x] T8 Tests de integración (migración `0008_document_practice.py`, `audit_checklist_from_pims` ante cambios en BD PIMS, revelación al intento 3, contrato OpenAPI, `test_architecture.py`) (AC-009-6, 9, 11, 15)
- [x] T9 Frontend: `types.ts`, `logic.ts` (+ `logic.test.ts`), `ReferencePanel.svelte` (lado a lado), 6 componentes accesibles en `src/lib/exercises/` e integración en `ExerciseForm.svelte` y módulo `+page.svelte` (AC-009-10, 13)
- [x] T10 E2E Playwright + `axe-core` sobre R3 lado a lado y formulario documental temporal con errores, revelación al 3er intento y aprobación (AC-009-13, 14)
- [x] T11 Documentación (`ADR-004`, `docs/c4/c3-componentes-api.md`, notas de cierre) y verificación completa `make verify` en verde (AC-009-15)

## Notas de cierre (Fase F8)
- `make verify` pasó al 100 %: `ruff`, `pyright` (0 errores), `prettier`, `svelte-check` (0 errores, 0 avisos), `pytest` (322 tests), `vitest` (23 tests), `playwright` E2E + `axe-core` (13 escenarios, 0 violaciones serias/críticas), `alembic check` (`0008_document_practice`) y `npm run build`.
- Plantillas de terceros en `raw/files/`: únicamente inspeccionadas en lectura; 0 archivos de `raw/` modificados o versionados; verificado sin coincidencias de 7-gramas ni identificadores literales del Anexo A.
- Conteo actual de módulos R2–R4 conservado (1 demo por ruta) con sidecar resuelto `04-declaracion-de-aplicabilidad.reference.md` en R3; el despliegue masivo de lecciones/ejercicios R2–R4 queda reservado para las Fases F9–F11.
