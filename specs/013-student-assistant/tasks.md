# Tareas 013 — Asistente flotante del estudiante

- [x] T1. Documentar contrato OpenAPI (`specs/013-student-assistant/contracts/openapi.yaml`) y prompt de sistema (`docs/ai/student_system_prompt.md`).
- [x] T2. Implementar capas `domain` y `application` del módulo `assistant` (entidades, guardrails anti-inyección y anti-soluciones, puertos y casos de uso).
- [x] T3. Implementar capa `infrastructure` (`AssistantMessageModel`, migración `0009_student_assistant.py`, repositorio SQLAlchemy, `PlatformStudentContextProvider`, `AgyStudentModelAdapter`), configuración en `core/config.py`, router HTTP y composición en `main.py`.
- [x] T4. Crear endpoints BFF SvelteKit (`/assistant/ask`, `/assistant/history`), componente accesible `AssistantWidget.svelte` y montaje global en `+layout.svelte`.
- [x] T5. Añadir pruebas unitarias (dominio + casos de uso + Vitest), integración API (`@pytest.mark.ac`), E2E Playwright + `axe-core` y actualizar `docs/c4/c3-componentes-api.md`.
- [x] T6. Ejecutar `make verify && make reset-demo` en verde y confirmar que no haya rastros en `raw/` ni `.env`.
