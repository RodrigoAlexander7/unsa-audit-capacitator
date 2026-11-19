# Tareas 014 — Modo administrador y propuestas de reestructuración

- [x] T1. Documentar contrato OpenAPI (`specs/014-admin-assistant-restructuring/contracts/openapi.yaml`) y prompts (`docs/ai/admin_advisor_prompt.md`, `docs/ai/admin_restructuring_prompt.md`).
- [x] T2. Implementar dominio (`assistant/domain/admin_cohort.py`), puertos y casos de uso administrativos en `assistant/application/`.
- [x] T3. Implementar `CurriculumProposalModel`, migración `0010_admin_proposals.py`, `SqlAlchemyAdminCohortProvider`, `SqlAlchemyCurriculumProposalRepository`, configuración en `core/config.py`, router `/assistant/admin/*` y composición en `main.py`.
- [x] T4. Crear proxies SvelteKit `/assistant/admin/*`, helper `resolveAliasesInText` y modo administrador + gestión de borradores en `AssistantWidget.svelte`.
- [x] T5. Añadir tests unitarios (`test_admin_assistant_domain.py`, `types.test.ts`), integración (`test_admin_assistant_api.py`), E2E (`admin-assistant.spec.ts`) y actualizar `docs/c4/c3-componentes-api.md`, `docs/demo.md` y `PLAN.md`.
- [x] T6. Ejecutar `make reset-demo && make verify && make reset-demo` en verde y confirmar que `raw/` y `.env` siguen sin versionar.
