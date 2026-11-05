# Plan 009 — Motor de práctica documental (F8)

**Estado:** aprobada (Fase F8).

---

## 1. Arquitectura y capas afectadas (`learning` + `seed` + `frontend`)

Se respeta estrictamente `domain ← application ← infrastructure / interface` (AC-001-5 / `test_architecture.py`).

### 1.1 `learning/domain` (puro, sin I/O ni frameworks)
- `route.py`:
  - Ampliar `ExerciseKind` con: `DOCUMENT_FORM`, `RISK_TABLE`, `TREATMENT_TABLE`, `AUDIT_CHECKLIST`, `NONCONFORMITY_FORM`, `COMPETENCE_MATRIX`.
  - Añadir a `Module`: `reference_title: str | None = None`, `reference_md: str | None = None`.
  - Añadir constante `REVEAL_AFTER_ATTEMPTS = 3`.
- Nuevo módulo puro dentro de `learning/domain/` (para mantener funciones cortas y sin duplicación):
  - `exercises.py`: punto único de entrada (`validate_spec`, `to_public`, `grade`, `solution_guide`, `GradeResult`, `ItemFeedback`, `SolutionGuideItem`) y los 6 tipos clásicos.
  - `document_exercises.py`: validadores, sanitizadores `to_public`, correctores deterministas y generadores de guía tras intentos agotados para los 6 nuevos tipos:
    - `document_form`: validación de campos tipados, normalización de texto (minúsculas + sin tildes para comparación determinista de rúbrica), evaluación de rúbrica (`min_words`, `criteria`, `forbidden_any`), evaluación declarativa de `cross_rules` (`date_order`, `disjoint`, `requires_if`, `unit_system_coherence`, `count_matches`).
    - `risk_table`: cálculo `riesgo = consequence + probability`, umbral `unacceptable_threshold` (default `3`), regla de datos sensibles (`sensitive_data=True` ⇒ `consequence == 2`), tolerancia acotada (sin permitir cruzar el umbral de aceptación) y explicación de desviación.
    - `treatment_table`: cálculo `residual_risk = residual_consequence + residual_probability`, validación de coherencia `option` ↔ `control_id` (y bandera `soa_applies` del catálogo) ↔ `residual_risk` ↔ `deadline` ↔ `owner`.
    - `audit_checklist`: verificación de `question_id`, `evidence_id` y `verdict` (`conforme`, `observacion`, `no_conformidad`) con retroalimentación diferenciada por dimensión.
    - `nonconformity_form`: validación por caso de separación `correction` vs `corrective_action`, `root_cause` vs síntoma, `requires_corrective_action`, desfase temporal `verification_date >= implementation_date + min_lag_days`, responsable y `doc_change_required` + `affected_document`.
    - `competence_matrix`: validación por fila de `competency_id`, `training_id`, `evidence_id` y regla de segregación/evaluador (`evaluator_position` ≠ cargo evaluado cuando corresponde).

### 1.2 `learning/application`
- `ports.py`:
  - Enriquecer `PositionFact` (`unit_code: str = ""`, `unit_name: str = ""`), `SystemFact` (`owner_unit_code: str = ""`, `data_categories: tuple[str, ...] = ()`), `PimsFact` (`expected_evidence: str = ""`, `summary: str = ""`), y añadir `ActivityFact` (`name`, `org_unit_code`, `org_unit_name`, `purpose`, `legal_basis`, `data_categories`, `retention`) en `UniversitySnapshot(activities: list[ActivityFact] = [])`.
  - Añadir a `LearningRepository`: `async def count_attempts(self, user_id: UUID, module_id: UUID) -> int` (y actualizar `InMemoryLearningRepository` y `SqlAlchemyLearningRepository`).
- `generators.py`:
  - Añadir generador `audit_checklist_from_pims(params, facts)` que construye la spec completa de `audit_checklist` a partir de `facts.pims` (`clause_ref` como dato, `expected_evidence`, estado real en BD) y distractores coherentes.
- `use_cases.py`:
  - `AttemptResult` incorpora `attempt_number: int = 1`, `solution_revealed: bool = False`, `solution_guide: tuple[SolutionGuideItem, ...] = ()`.
  - `SubmitAttempt.execute`: consulta `prior = await self._repo.count_attempts(user_id, module_id)`, calcula `attempt_number = prior + 1`, registra el intento y solo adjunta `solution_guide` cuando `not passed and attempt_number >= reveal_after` (donde `reveal_after = spec.get("reveal_after_attempts", REVEAL_AFTER_ATTEMPTS)`).

### 1.3 `learning/infrastructure`
- `models.py` + migración Alembic `0008_document_practice.py` (revisa `0007_advisor_queries.py`):
  - Añadir `modules.reference_title` (`String(200)`, nullable) y `modules.reference_md` (`Text`, nullable).
- `sqlalchemy_repository.py`:
  - Persistir/leer `reference_title` y `reference_md` en `ModuleModel`.
  - Implementar `count_attempts(user_id, module_id)` con `SELECT count(*)`.
- `content_loader.py`:
  - Soportar `reference_doc: <code>` en frontmatter de `NN-slug.md` (lee el `document.yaml` + último `vN.md` de `content/institutional/<code>/`) o archivo hermano `NN-slug.reference.md` (título desde frontmatter o primer `#` + cuerpo).
  - Validar que todo módulo con ejercicio pase `validate_spec` (y que `reference_md` no esté vacío si se declara).
- `sqlalchemy_university_facts.py` y `learning_facts.py`:
  - Poblar los campos enriquecidos de `PositionFact`, `SystemFact`, `ActivityFact` (desde `ProcessingActivityModel`) y `PimsFact` (`expected_evidence`, `summary`).

### 1.4 `learning/interface`
- `router.py`:
  - `ModuleReferenceResponse(title: str, body_md: str)` y campo opcional `reference: ModuleReferenceResponse | None = None` en `ModuleResponse`.
  - `SolutionGuideItemResponse(id: str, label: str, expected_summary: str)` y campos opcionales `attempt_number: int`, `solution_revealed: bool`, `solution_guide: list[SolutionGuideItemResponse] | None = None` en `AttemptResponse`.
- Contrato OpenAPI: `specs/009-document-practice/contracts/openapi.yaml` documentando los esquemas ampliados de `GET /modules/{module_id}` y `POST /modules/{module_id}/attempts`.

### 1.5 `seed/`
- `seed/solutions.py`:
  - Ampliar `solve(kind, spec)` y `wrong(kind)` para los 6 nuevos tipos, garantizando `solve` = 100 puntos y `wrong` = formato válido con 0 (o < `pass_score`).

### 1.6 `frontend/` (Svelte 5 runes, TypeScript, tema claro único)
- `src/lib/exercises/types.ts`: tipos TypeScript de specs públicas y respuestas para los 6 nuevos tipos + `ModuleReference` + `SolutionGuideItem` en `AttemptResult`.
- `src/lib/exercises/logic.ts` (+ `logic.test.ts`): `initialAnswer`, `completion`, `canSubmit` y cálculo auxiliar de riesgo (`C + P`) para feedback visual inmediato sin sustituir al backend.
- 6 componentes accesibles nuevos en `src/lib/exercises/`:
  - `DocumentForm.svelte` (secciones, inputs tipados, multiselect por checkboxes en `<fieldset>`, mensajes de error/reglas cruzadas con `role="alert"`).
  - `RiskTable.svelte` (tabla responsiva con selectores `0/1/2`, cálculo visual en vivo de nivel y etiqueta Aceptable/No aceptable, alertas por fila).
  - `TreatmentTable.svelte` (opción, control SoA, responsable, plazo, residual `C/P` con nivel residual en vivo).
  - `AuditChecklist.svelte` (cláusula como dato, contexto observado, pregunta, evidencia y veredicto).
  - `NonconformityForm.svelte` (corrección vs acción correctiva, causa raíz, fechas, cambio documental).
  - `CompetenceMatrix.svelte` (cargo → competencia → capacitación → evidencia → evaluador).
- `src/lib/exercises/ExerciseForm.svelte`: integra los 6 componentes, muestra alerta de intentos agotados y bloque `solution_guide` cuando `result.solution_revealed` sea `true`.
- `src/lib/exercises/ReferencePanel.svelte` y `src/routes/routes/[code]/[module]/+page.svelte`: vista lado a lado «Ejemplo resuelto (UNSA) / Tu documento» cuando `mod.reference` está presente (CSS Grid 2 columnas en escritorio ≥ 1024 px, pestañas o apilado accesible en pantallas pequeñas).

---

## 2. Contrato de esquemas privados vs públicos (resumen)

### `document_form`
- **Spec privada:** `{ prompt, scenario, document_title, reveal_after_attempts?, sections: [{id, title, description?, fields: [{id, label, type, required, help?, placeholder?, options?, validation: {...}}]}], cross_rules: [{id, kind, label, fields, params?, feedback}] }`
- **Spec pública (`to_public`):** mantiene `prompt`, `scenario`, `document_title`, `sections` y en cada field solo `{id, label, type, required, help?, placeholder?, options?}`; elimina `validation` y `cross_rules`.
- **Answer:** `{ fields: Record<string, string | string[]> }`

### `risk_table`
- **Spec privada:** `{ prompt, scenario, threshold?: 3, rows: [{id, asset, asset_owner, data_categories, existing_controls, sensitive_data: bool, threat, vulnerability, risk_owner, threat_options?, vulnerability_options?, risk_owner_options?, expected_threat?, expected_vulnerability?, expected_risk_owner?, expected_consequence, expected_probability, tolerance?: 0, explanation}] }`
- **Spec pública:** mantiene datos del escenario y `*_options`, elimina `expected_*`, `tolerance`, `explanation` y `sensitive_data`? *(Nota: `data_categories` ya es dato visible del escenario; `sensitive_data` es regla de dominio privada si no se quiere dar pista directa, aunque el alumno ve `data_categories: ["datos de salud"]`.)*
- **Answer:** `{ rows: Record<string, { threat?: string, vulnerability?: string, risk_owner?: string, consequence: number, probability: number }> }`

### `treatment_table`
- **Spec privada:** `{ prompt, scenario, options: Opt[], soa_controls: [{id, label, soa_applies: bool}], owners: Opt[], rows: [{id, asset, threat, vulnerability, initial_consequence, initial_probability, initial_risk, valid_options, allow_accept, valid_controls, valid_owners, min_deadline, max_deadline, expected_option, expected_control, expected_owner, expected_deadline, expected_residual_c, expected_residual_p, residual_tolerance?: 0, explanation}] }`
- **Spec pública:** `options`, `soa_controls` solo `{id, label}` (¡sin `soa_applies`!), `owners`, y datos iniciales de cada fila sin `valid_*` ni `expected_*`.
- **Answer:** `{ rows: Record<string, { option: string, control_id: string, owner: string, deadline: string, residual_consequence: number, residual_probability: number }> }`

### `audit_checklist`
- **Spec privada:** `{ prompt, scenario, verdicts: Opt[], items: [{id, clause_ref, requirement_title, observed_context, questions: Opt[], evidences: Opt[], expected_question, expected_evidence, expected_verdict, explanation}] }`
- **Spec pública:** elimina `expected_*` y `explanation`.
- **Answer:** `{ items: Record<string, { question_id: string, evidence_id: string, verdict: string }> }`

### `nonconformity_form`
- **Spec privada:** `{ prompt, scenario, documents: Opt[], positions: Opt[], cases: [{id, title, detection_context, detection_date, correction_options: Opt[], root_cause_options: Opt[], action_options: Opt[], verification_options: Opt[], expected_correction, expected_root_cause, expected_requires_action: bool, expected_action, expected_responsible, min_verification_lag_days, max_implementation_date, expected_verification, expected_doc_change: bool, expected_document?, explanation}] }`
- **Spec pública:** elimina `expected_*`, `min_verification_lag_days`, `max_implementation_date`, `explanation`.
- **Answer:** `{ cases: Record<string, { correction: string, root_cause: string, requires_action: boolean, action: string, responsible: string, implementation_date: string, verification_date: string, verification: string, doc_change: boolean, affected_document: string }> }`

### `competence_matrix`
- **Spec privada:** `{ prompt, scenario, competencies: Opt[], trainings: Opt[], evidences: Opt[], evaluators: Opt[], rows: [{id, position_title, role_summary, expected_competency, expected_training, expected_evidence, forbidden_evaluators?: string[], valid_evaluators?: string[], expected_evaluator?, explanation}] }`
- **Spec pública:** elimina `expected_*`, `forbidden_evaluators`, `valid_evaluators`, `explanation`.
- **Answer:** `{ rows: Record<string, { competency_id: string, training_id: string, evidence_id: string, evaluator_id?: string }> }`

---

## 3. Documentación y cierre de fase
- Crear `docs/adr/ADR-004-correccion-determinista-documentos.md`.
- Actualizar `docs/c4/c3-componentes-api.md` con los nuevos componentes y capacidades de `learning`.
- Ejecutar `make verify` completo en verde (ruff, pyright, alembic check, pytest, prettier, svelte-check, vitest, build, Playwright + axe).
