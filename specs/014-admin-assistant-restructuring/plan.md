# Plan 014 — Modo administrador y propuestas de reestructuración

## Diseño por capas (Clean Architecture)

### Backend (`backend/src/unsa_audit/assistant/`)
1. **Domain (`domain/admin_cohort.py`)**:
   - Entidades inmutables: `LearnerAliasSummary`, `AdminCohortSnapshot`, `CurriculumProposal`, `ProposalStatus` (`draft | accepted | discarded`), `ProposalChangeType`.
   - Funciones puras:
     - `pseudonymize_admin_question(question, learners)`: reemplaza ocurrencias de `email` y `full_name` (con/sin acentos) por su alias `P-xx`.
     - `build_admin_cohort_prompt(system_prompt, snapshot, question)`: arma `<CONTEXTO_COHORTE>` sin PII + `<PREGUNTA_ADMIN>` escapada y su hash SHA-256.
     - `build_restructuring_prompt(system_prompt, snapshot, focus, route_code)`: solicita salida JSON estructurada (`{summary, proposals[]}`).
     - `parse_restructuring_proposals(raw_text, valid_route_codes, ...)`: extrae JSON (incluyendo bloques ```json), valida campos obligatorios y normaliza `change_type` (lanza `ProposalParseError` si es inválido).
2. **Application (`application/admin_ports.py`, `application/admin_use_cases.py`)**:
   - Puertos: `AdminCohortProvider`, `CurriculumProposalRepository`.
   - Casos de uso: `GetAdminCohortSummary`, `AskAdminAssistant`, `ListAdminHistory`, `ClearAdminHistory`, `GenerateRestructuringProposals`, `ListCurriculumProposals`, `ReviewCurriculumProposal`.
3. **Infrastructure (`infrastructure/`)**:
   - `models.py`: añade `CurriculumProposalModel` (`curriculum_proposals`).
   - `admin_cohort_provider.py`: `SqlAlchemyAdminCohortProvider` consulta `users (role='learner')`, `enrollments`, `modules`, `module_progress`, `exercise_attempts` y `assessments`, además de métricas agregadas por ruta/módulo para alimentar decisiones de reestructuración.
   - `proposal_repository.py`: `SqlAlchemyCurriculumProposalRepository`.
   - Migración `0010_admin_proposals.py` (`down_revision = "0009"`).
4. **Interface (`interface/admin_router.py`) + composición (`main.py`)**:
   - Router `/assistant/admin/*` protegido por `SuperAdmin`.
   - Prompts: `docs/ai/admin_advisor_prompt.md` y `docs/ai/admin_restructuring_prompt.md`.

### Frontend (`frontend/src/`)
1. **Proxies SvelteKit (`routes/assistant/admin/`)**:
   - `cohort/+server.ts`, `ask/+server.ts`, `history/+server.ts`, `proposals/+server.ts`, `proposals/generate/+server.ts`, `proposals/[id]/+server.ts`, validando `locals.user.role === 'superadmin'`.
2. **UI dual (`lib/assistant/`)**:
   - `types.ts`: tipos de cohorte/alias/propuestas + `resolveAliasesInText` (mapeo local `P-xx` → nombre real en respuestas).
   - `AssistantWidget.svelte`: pestañas «Estudiante» y «Administrador» para superadmin, resumen de cohorte seudónimo con enlace local, chips de consulta, botón «Proponer reestructuración» y gestión de borradores (`Aceptar` / `Descartar`).

### Documentación y pruebas
- Tests unitarios: `test_admin_assistant_domain.py`, `types.test.ts`.
- Tests integración: `test_admin_assistant_api.py` (`@pytest.mark.ac`).
- E2E Playwright + `axe-core`: `e2e/admin-assistant.spec.ts`.
- Actualización final de `docs/c4/c3-componentes-api.md`, `docs/demo.md` y `PLAN.md`.
