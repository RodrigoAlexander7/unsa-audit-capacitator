# Plan 006 — Rutas 2–4 y evaluación controller/processor

## `learning` (ampliación)
- `Module.planned` (frontmatter `planned: true`; columna `modules.planned`); validación del loader: planned ⇒ no obligatorio y sin ejercicio.
- `ModuleStatus`: un módulo planned siempre `locked`; error de aplicación `ModulePlanned` (409). `route_completed` exige ≥ 1 módulo publicado.
- Vistas: `RouteSummary.modules_planned`; `modules_total` = publicados.
- `ExerciseKind.SOA_FORM` con `validate/to_public/grade` (crédito parcial).
- `UniversitySnapshot.pims` (lista de `PimsFact`) + generador `pims_audit_findings`. Adaptador `LearningFacts` compone el snapshot de la universidad con el de `GetPimsCompleteness` (documents) sin que `learning` conozca sus tablas.
- Contenido: 3 módulos demo + módulos `planned` para completar la estructura (8/9/10).

## `assessment` (módulo nuevo, Clean Architecture)
- domain: `Profile`, `Question`, `AssessmentDefinition`, `grade()` → `AssessmentResult` (competencias y requisitos), `Attempt`.
- application: puertos `QuestionBank`, `AssessmentRepository`; casos de uso `StartAssessment`, `SubmitAssessment`, `GetAssessment`, `ListAssessments`.
- infrastructure: `FileQuestionBank` (lee `content/assessment/<perfil>.json`, validado contra `pims/requirements.yaml`), ORM `assessments` (JSONB), repositorio.
- interface: `/assessments` (crear, listar), `/assessments/{id}`, `/assessments/{id}/submit`.

## Decisiones
- **Una evaluación = intento fijo:** `POST /assessments` fija las preguntas y su orden (semilla = id del intento); `submit` corrige una sola vez. Sustituye a los endpoints `answers`/`finish` del PLAN §9 (más simple y sin estado intermedio).
- Las definiciones viven en contenido (no en BD); el intento guarda ids de pregunta, respuestas y el resultado calculado (incluidas las correcciones), de modo que el historial no cambia si luego se edita el banco.
- La competencia y el requisito de cada pregunta son **datos**; el requisito referencia `pims_requirements.code` para enlazar con el conjunto documental y alimentar analytics por cláusula (F6).
- Cada ruta 2–4 desarrolla un único módulo obligatorio (el demo); las horas acreditadas son las de ese módulo.
- No hay prerrequisito para la evaluación (cualquier usuario autenticado).

## Migraciones
0006: `modules.planned` (default false) y tabla `assessments`.

## Frontend
- Ruta: módulos `planned` como "Próximamente"; tarjetas con "N módulos · M en preparación"; aviso sobre las horas del POC.
- `SoaForm.svelte` (+ lógica `completion/canSubmit`), resto de componentes reutilizados.
- `/assessment` (perfiles + historial) y `/assessment/[id]` (responder / resultados con barras por competencia y tabla por requisito → `/documents/pims`).

## Tests
- Unit: `soa_form` (validación, pública, puntaje), planned (progreso/estado), generador de auditoría, contenido de rutas 2–4 y bancos, `grade` de evaluación y casos de uso con repositorio en memoria.
- Integración: cadena R1→R4 con 21 h, gating, planned 409, `/assessments` completo, contrato.
