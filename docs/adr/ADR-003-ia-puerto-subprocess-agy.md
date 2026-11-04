# ADR-003 — IA mediante puerto y subprocess de `agy`

- **Estado:** aceptada (flags finales por confirmar en el spike de la Fase 6)
- **Fecha:** 2026-11-11

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
