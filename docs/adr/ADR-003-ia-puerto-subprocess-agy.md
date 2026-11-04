# ADR-003 — IA mediante puerto y subprocess de `agy`

- **Estado:** aceptada; flags confirmados por el spike de la Fase 6 (2026-11-11)
- **Fecha:** 2026-11-11

## Resultado del spike (Fase 6)
- `agy --print "<prompt>" --output-format json --mode plan --sandbox --effort low --print-timeout 120s`, sin stdin y en un directorio vacío, imprime un JSON `{"conversation_id", "status": "SUCCESS", "response": "...", "duration_seconds", "num_turns", "usage"}`. Sin API key.
- El prompt va como **un único argumento** posicional tras `--print`; no hace falta stdin.
- Latencia observada: ~2,5 s para un prompt trivial y ~9 s con el snapshot completo.
- Adaptador: `analytics/infrastructure/agy_advisor.py` (`AgyCliAdvisor`): entorno por lista blanca, directorio temporal vacío, lectura de stdout acotada (256 KiB), respuesta truncable, timeout con `kill`; `status ≠ SUCCESS`, JSON inválido o código de salida ≠ 0 → `AdvisorUnavailable`.
- Verificación manual con `agy` real: la pregunta «¿Cómo están los alumnos de sensibilización?» devolvió un diagnóstico fiel a los datos (incluso con 0 matriculados: indicó que los datos no alcanzaban). Las pruebas automáticas usan un script falso que imita este contrato.

## Contexto
El superadmin consulta a una IA sobre estadísticas de las rutas. Para el POC se usa `agy` (Antigravity CLI) por terminal, **sin API key**.

## Decisión
- Puerto `AnalyticsAdvisorPort` en `application`; adaptador `AgyCliAdapter` en `infrastructure`.
- Invocación en modo no interactivo (`agy --print ... --output-format json --mode plan --sandbox`), con `asyncio.create_subprocess_exec` **sin shell**, timeout, límite de salida y directorio de trabajo vacío. Nunca `--dangerously-skip-permissions`.
- El contexto enviado es un snapshot **agregado y anonimizado**; no incluye nombres ni emails.
- Cada consulta se registra en `advisor_queries`.
- Tests con `FakeAgyAdapter` y un script falso que imita a `agy`; CI no depende de `agy` real.
- Fallback: exportar el snapshot para consultarlo manualmente.

## Consecuencias
+ Cambiar a una API de LLM implica solo otro adaptador.
− Dependencia de la CLI local y de su estabilidad de flags; mitigado con configuración por `.env` y el spike.
