# Especificación 014 — Modo administrador y propuestas de reestructuración

## Objetivo

Ampliar el asistente flotante para que el superadministrador pueda consultar en el mismo popup el avance individual y colectivo de los participantes mediante alias seudónimos (`P-01`, `P-02`, ...), ver en su navegador los nombres reales resueltos localmente y generar borradores revisables de reestructuración del plan formativo sin exponer PII a `agy` ni mutar el currículo automáticamente.

## Criterios de aceptación

- **AC-014-1 (Autorización exclusiva de superadministrador)**: Todos los endpoints `/assistant/admin/*` y los proxies SvelteKit equivalentes requieren sesión con rol `superadmin` (`401` sin sesión, `403` para participantes). En el widget flotante, el selector de modo solo se renderiza cuando `user.role === 'superadmin'`.
- **AC-014-2 (Seudonimización estricta de estudiantes)**: El snapshot de cohorte y los prompts enviados al modelo IA identifican a cada participante únicamente por un alias determinista `P-01`, `P-02`, ... nunca por `full_name`, `email` ni `user_id`. Si el administrador escribe un nombre o correo real en su pregunta, el dominio lo sustituye por su alias `P-xx` antes de registrar o invocar a `agy`.
- **AC-014-3 (Resolución local de alias para el UI)**: `/assistant/admin/cohort` y `/assistant/admin/ask` devuelven la tabla `aliases` con el mapeo `{alias, full_name, email, stalled, overall_progress_pct}` solo al superadministrador autenticado. El cliente resuelve localmente cada `P-xx` en las respuestas para mostrar el nombre real al coordinador sin que haya salido hacia `agy`.
- **AC-014-4 (Generación de borradores estructurados de reestructuración)**: `POST /assistant/admin/proposals/generate` solicita a `agy` propuestas estructuradas en JSON basadas en métricas del cohorte y rutas, valida el esquema en dominio (error `502` si la salida no es interpretable) y persiste 1–3 registros en `curriculum_proposals` (migración `0010`) con estado inicial `draft`, sin modificar `routes` ni `modules`.
- **AC-014-5 (Revisión de borradores)**: `GET /assistant/admin/proposals` lista las propuestas almacenadas y `PATCH /assistant/admin/proposals/{id}` permite cambiar su estado entre `draft`, `accepted` y `discarded` con nota opcional (`404` inexistente, `422` estado inválido).
- **AC-014-6 (Historial separado y validación del modo admin)**: `POST /assistant/admin/ask`, `GET /assistant/admin/history` y `DELETE /assistant/admin/history` operan sobre `role="admin"` con validación de entrada (`1..800` chars, `422`), defensa anti-inyección y registro de fallos (`502`).
- **AC-014-7 (UI dual en popup flotante y accesibilidad)**: El superadministrador puede alternar mediante pestañas accesibles entre «Estudiante» y «Administrador» dentro del popup global, consultar avances con alias resueltos localmente, generar y revisar propuestas de reestructuración y pasar `axe-core` (WCAG 2.1 AA, tema claro) sin violaciones serias ni críticas.
