---
title: Riesgos de privacidad
minutes: 140
---

# Riesgos de privacidad

> Material formativo para este POC (datos 100 % ficticios de la UNSA). Las referencias a cláusulas se tratan como dato parametrizable según la edición vigente.

Un error frecuente en auditoría es evaluar los riesgos **solo desde el daño financiero o reputacional de la organización**. ISO/IEC 27701 extiende el análisis de seguridad de la información para exigir que la consecuencia refleje ante todo **el impacto sobre las personas titulares de los datos** (discriminación, exposición médica, fraude bancario o pérdida de derechos).

## Reglas interpretativas de la metodología UNSA

1. **Separar activo, amenaza, vulnerabilidad y propietario:** cada activo tratado dentro del alcance requiere identificar quién puede dañarlo (amenaza), qué debilidad permite el incidente (vulnerabilidad) y qué cargo tiene autoridad para decidir su tratamiento (propietario del riesgo).
2. **Escala objetiva (`C + P` de 0 a 4):**
   - **Consecuencia (`0–2`):** `0` impacto despreciable sobre el titular; `1` molestias o perjuicio moderado; `2` daño grave sobre los derechos, salud o patrimonio del titular.
   - **Regla de datos sensibles:** cuando un activo trata categorías sensibles (p. ej. salud, datos socioeconómicos críticos o antecedentes equivalentes), la metodología institucional fija **consecuencia = `2` (alta)** sin excepciones.
   - **Probabilidad (`0–2`):** depende de la solidez real de los controles ya desplegados (`0` controles sólidos, `1` parciales/razonables, `2` débiles o ausentes).
3. **Umbral de aceptación (`< 3`):** niveles `0–2` son **aceptables** bajo monitoreo; niveles **`3` y `4` no son aceptables** y exigen planificar tratamiento.

## Ejemplo resuelto y práctica

Revisa a la izquierda la valoración modelo sobre dos activos de la UNSA y luego completa la matriz de riesgos de cuatro sistemas reales de la universidad.
