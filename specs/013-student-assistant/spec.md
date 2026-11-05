# Especificación 013 — Asistente flotante del estudiante

## Objetivo

Incorporar un asistente pedagógico flotante disponible en toda página autenticada para ayudar al participante a comprender ISO/IEC 27701 (sobre ISO/IEC 27001), ISO 19011 y su aplicación a la UNSA ficticia, utilizando el entorno actual (lección y documento de referencia) sin filtrar nunca soluciones de ejercicios ni datos personales.

## Criterios de aceptación

- **AC-013-1 (Clean Architecture y persistencia)**: El módulo backend `assistant` separa `domain`, `application`, `infrastructure` e `interface` sin dependencias de frameworks ni subprocess en `domain`/`application`, y persiste el historial en la tabla `assistant_messages` (migración Alembic `0009`).
- **AC-013-2 (Contexto UNSA, lección y cero fugas)**: Al consultar `/assistant/ask`, el proveedor de contexto recoge únicamente hechos públicos de la UNSA ficticia (unidades, cargos sin PII estudiantil, sistemas, actividades de tratamiento), resumen del estado documental del PIMS y el extracto de la lección/referencia del módulo indicado (`module_id` o `route_path`). Nunca lee ni inyecta especificaciones, claves, rubricas ni respuestas de `.exercise.json`, ni correos/nombres de participantes.
- **AC-013-3 (Guardrails anti-inyección y anti-trampas)**: Preguntas que pidan respuestas exactas/claves para aprobar ejercicios o intenten anular instrucciones / revelar prompts del sistema son detectadas de forma determinista antes de invocar al modelo, devolviendo `status="refused"` con orientación pedagógica y sin ejecutar `agy`. Las entradas válidas se delimitan y escapan como datos no confiables.
- **AC-013-4 (Aislamiento estricto del historial)**: Cada consulta queda ligada al `user_id` autenticado (`role="student"`). `GET /assistant/history` devuelve únicamente el historial propio (más reciente primero) y `DELETE /assistant/history` elimina solo las filas del usuario solicitante.
- **AC-013-5 (Contrato HTTP y manejo de fallos)**: Los endpoints `/assistant/ask`, `/assistant/history` (`GET`, `DELETE`) exigen sesión JWT válida (`401` si falta), validan pregunta no vacía y ≤ 800 caracteres (`422` sin invocar al modelo) y traducen fallos/timeouts del subproceso a `502 Bad Gateway` registrando el error en historial.
- **AC-013-6 (Widget flotante global y accesibilidad)**: Toda página autenticada muestra el disparador flotante inferior derecho «Asistente UNSA» (oculto sin sesión). Al abrirse despliega un `<dialog>` no modal (`popover="manual"` con respaldo `show()`) en tema claro con contexto automático de página/módulo, sugerencias iniciales, renderizado Markdown seguro, región de historial con botón de limpieza, cierre con `Escape` y retorno de foco al disparador, con cero violaciones serias o críticas en `axe-core`.
