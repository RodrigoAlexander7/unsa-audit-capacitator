# Tasks 007 — Analytics y asesor IA

- [x] T1 Contrato `contracts/openapi.yaml` y ADR-003 actualizado con el spike (AC-007-9)
- [x] T2 domain + application: estadísticas, snapshot, prompt, `AskAdvisor` + unit tests (AC-007-4, 8)
- [x] T3 infrastructure: repositorio SQL agregado, `advisor_queries` (migración 0007) (AC-007-1..3, 7)
- [x] T4 infrastructure: `AgyCliAdvisor` + script falso + tests (AC-007-5)
- [x] T5 `docs/ai/system_prompt.md` (AC-007-8)
- [x] T6 interface: `/admin/stats/*`, `/admin/advisor/*` + wiring (AC-007-1..7)
- [x] T7 tests de integración con datos reales y permisos (AC-007-1..7)
- [x] T8 Frontend `/admin` y `/admin/advisor` (AC-007-11)
- [x] T9 Smoke manual con `agy` real (AC-007-12)
- [x] T10 Verificación completa, docs y commit único de la fase (AC-007-10)

## Notas de cierre
- Verificado: ruff, pyright, `alembic check`, **291 tests backend** (192 unit + 99 integración con Postgres real), svelte-check, 18 vitest y build.
- **AC-007-12 (manual, `agy` real):** `POST /admin/advisor/ask` devolvió en ~9 s un diagnóstico en el formato *Diagnóstico / Ajustes propuestos*. Con la BD de desarrollo sin participantes la IA indicó correctamente que los datos no alcanzaban; la comprobación con datos demo se repite en la Fase 7.
- Seguridad del adaptador probada: el prompt con `$(…)`, comillas, saltos de línea y `--flag` llega como un único argumento sin ejecutar nada; el entorno no hereda `JWT_SECRET`; timeout mata el proceso.
- El snapshot se verificó sin nombres, emails ni `@` (tests de dominio y de integración).
- UI del panel y del asesor: comprobación visual en la Fase 7 con datos demo.
- Pendiente: ver evolución en el tiempo (series) y seguimiento individual, fuera de alcance.
