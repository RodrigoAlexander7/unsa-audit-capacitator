# Plan 013 — Asistente flotante del estudiante

## Diseño de arquitectura

### Backend (`backend/src/unsa_audit/assistant/`)
1. **Domain (`domain/`)**:
   - `entities.py`: `AssistantMessage`, `AssistantStatus` (`ok | refused | error`), `PromptContext`, `MAX_ASSISTANT_QUESTION_CHARS = 800`.
   - `guardrails.py`: validación de pregunta, detección determinista de inyección de prompts y solicitud de respuestas/soluciones, sanitización de delimitadores en entradas, construcción canónica de prompt (`<CONTEXTO>` + `<PREGUNTA_ESTUDIANTE>`) con hash SHA-256 sin PII ni ejercicios, y filtrado básico de salida.
2. **Application (`application/`)**:
   - `errors.py`: `AssistantError`, `InvalidAssistantQuestion`, `AssistantUnavailable`, `AssistantTimeout`.
   - `ports.py`: `StudentContextSnapshot`, `StudentContextProvider`, `ModelAnswer`, `AssistantModelPort`, `AssistantHistoryRepository`.
   - `use_cases.py`: `AskStudentAssistant`, `ListStudentHistory`, `ClearStudentHistory`.
3. **Infrastructure (`infrastructure/`)**:
   - `models.py`: `AssistantMessageModel` (`assistant_messages`, FK `users.id ON DELETE CASCADE`).
   - `sqlalchemy_repository.py`: persistencia y limpieza aislada por `(user_id, role)`.
   - `context_provider.py`: `PlatformStudentContextProvider` consumiendo puertos (`UniversityFacts`, `LearningRepository`, `DocumentRepository`) sin leer nunca `Module.exercise`.
   - `agy_adapter.py`: `AgyStudentModelAdapter` reutilizando `AgyCliAdvisor` y traduciendo excepciones al puerto del asistente.
   - `backend/alembic/versions/0009_student_assistant.py` + registro del modelo en `backend/alembic/env.py`.
4. **Interface (`interface/`) + composición (`main.py`)**:
   - `router.py`: `POST /assistant/ask`, `GET /assistant/history`, `DELETE /assistant/history`.
   - `docs/ai/student_system_prompt.md` + `Settings.student_assistant_prompt_path` en `core/config.py`.
   - `create_app(..., assistant: AssistantModelPort | None = None)` para pruebas rápidas deterministas.

### Frontend (`frontend/src/`)
1. **BFF SvelteKit (`routes/assistant/`)**:
   - `ask/+server.ts` (`POST`) y `history/+server.ts` (`GET`, `DELETE`) reenvían el JWT de la cookie `httpOnly` hacia FastAPI.
2. **Componente global (`lib/assistant/AssistantWidget.svelte`)**:
   - Renderizado en `+layout.svelte` dentro de `<aside aria-label="Asistente de capacitación">` solo si `data.user` existe.
   - Usa `<dialog popover="manual">` con fallback `dialog.show()`/`close()`, botón visible «Asistente UNSA» y «Cerrar», `aria-expanded`, retorno de foco y cierre con `Escape`.
   - Detecta automáticamente `page.params.module` y `page.url.pathname` para contextualizar las consultas.
   - Reutiliza `renderMarkdown` para respuestas seguras en tema claro.

### Documentación y pruebas
- Unitarias: guardrails (inyección, fuga de soluciones, sanitización), casos de uso con dobles falsos, validación arquitectónica automática (`test_architecture.py`).
- Integración: aislamiento por usuario, borrado de historial, ausencia de PII y `.exercise.json` en el prompt recibido por el modelo falso, códigos HTTP `401/422/502/200`.
- E2E Playwright + `axe-core`: visibilidad global en rutas autenticadas, ocultación en `/login`, consulta con rechazo pedagógico real contra PostgreSQL + limpieza de historial, consulta simulada con Markdown y verificación WCAG AA.
- Actualización de `docs/c4/c3-componentes-api.md` y `backend/tests/integration/conftest.py` (`_TABLES`).
