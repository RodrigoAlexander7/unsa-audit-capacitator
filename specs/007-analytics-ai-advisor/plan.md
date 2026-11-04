# Plan 007 — Analytics y asesor IA

## Módulo `analytics` (Clean Architecture)
- **domain:** dataclasses `RouteStats`, `ModuleStats`, `AssessmentProfileStats`, `GroupAverage`, `AdvisorQuery`; funciones puras `hardest_modules`, `percent`.
- **application:**
  - Puertos: `AnalyticsReadRepository` (consultas agregadas), `AnalyticsAdvisorPort`, `AdvisorQueryRepository`, `PimsSummaryProvider`.
  - Casos de uso: `GetRouteStats`, `GetRouteDetailStats`, `GetAssessmentStats`, `BuildSnapshot` (agregado + anonimizado + hash), `AskAdvisor`, `ListAdvisorHistory`.
  - `prompt.py`: arma el prompt (sistema + snapshot + pregunta).
- **infrastructure:** `SqlAlchemyAnalyticsRepository` (SQL agregado sobre las tablas de learning/assessment/identity), `AgyCliAdvisor` (subprocess), ORM `advisor_queries`, `PimsSummaryAdapter` (usa `GetPimsCompleteness` y las solicitudes abiertas de documents).
- **interface:** router `/admin/stats/*` y `/admin/advisor/*` con `SuperAdmin`.

## Decisiones
- **Lectura agregada en SQL** (no se cargan filas de personas): garantiza el anonimato por construcción; el snapshot nunca recibe ids de usuario.
- **Estancado = matriculado en curso sin intentos en los últimos 7 días** (reloj inyectable para tests).
- **Dificultad de un módulo** = menor tasa de aprobación entre los módulos con ≥ 3 intentos.
- **Adaptador `agy`:** `[cmd…, "--print", prompt, flags…, "--print-timeout", "<n>s"]`; `AGY_COMMAND` admite un comando compuesto (`shlex`); entorno por lista blanca (`PATH`, `HOME`, `LANG`, `TERM`, `XDG_*`); `asyncio.create_subprocess_exec`; `wait_for` + `kill`; lectura acotada de stdout (256 KiB) y de la respuesta (configurable, 8 000 caracteres por defecto).
- **Salida de la IA** como Markdown con secciones *Diagnóstico* y *Ajustes propuestos*; la UI la renderiza con `renderMarkdown` (sanea HTML).
- **Registro** en `advisor_queries` (migración 0007) incluye errores.
- **Pruebas sin `agy` real:** script falso ejecutable que imita su contrato (éxito, error, timeout, JSON inválido); un smoke manual con `agy` real queda documentado.

## Datos
`advisor_queries(id, asked_by FK users SET NULL, question, snapshot_hash, status[ok|error], answer, error, duration_ms, created_at)`.

## Frontend
`/admin` (resumen, tabla por ruta, módulos difíciles, evaluaciones por competencia y por requisito, PIMS) y `/admin/advisor` (formulario, preguntas de ejemplo, respuesta, historial, descarga del snapshot). Guardas de rol en las cargas del servidor.

## Tests
- Unit: dominio (`hardest_modules`), anonimato del snapshot, armado del prompt, `AskAdvisor` con asesor falso, adaptador `agy` contra script falso.
- Integración: datos reales de varios participantes → estadísticas, permisos 401/403/404/422/502, registro de consultas, snapshot sin PII, contrato.
