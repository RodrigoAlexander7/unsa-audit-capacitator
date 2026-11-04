# Spec 007 — Analytics y asesor IA (`agy`)

**Estado:** aprobada (plan v2, Fase 6)

## Objetivo
Que el **superadmin** vea el estado de las 4 rutas y de las evaluaciones, y pueda preguntar a una IA (`agy`, CLI de Antigravity, sin API key) cosas como *«¿Cómo están los alumnos de sensibilización?»* y recibir un diagnóstico con **ajustes propuestos al plan de enseñanza**, a partir de datos **agregados y anonimizados**.

## Spike previo (hecho)
`agy --print "<prompt>" --output-format json --mode plan --sandbox --effort low --print-timeout 120s` (sin stdin, en un directorio vacío) responde en ~2,5 s con `{"status":"SUCCESS","response":"…","duration_seconds":…,"usage":{…}}`. Sin API key. El prompt va como un único argumento (sin shell).

## Historias
- **H1.** Como superadmin quiero ver por ruta cuántas personas hay, cuántas avanzan, cuántas terminan y cuántas se estancan.
- **H2.** Como superadmin quiero saber qué módulos son más difíciles (menor puntaje y tasa de aprobación).
- **H3.** Como superadmin quiero ver en qué competencias y requisitos del PIMS fallan más los participantes de las evaluaciones.
- **H4.** Como superadmin quiero hacer preguntas en lenguaje natural y recibir propuestas de ajuste del plan.
- **H5.** Como superadmin quiero poder exportar el *snapshot* para consultarlo manualmente en una terminal.

## Reglas de negocio
1. Todo lo de este módulo es **solo superadmin** (401 sin token, 403 para `learner`).
2. Las estadísticas se calculan sobre participantes con rol `learner` (el superadmin no cuenta).
3. **Por ruta:** matriculados, en curso, completados, % de finalización, avance medio (% de módulos publicados completados), horas acreditadas por matriculado, intentos de ejercicios, % de intentos aprobados y **estancados** (matriculados en curso sin intentos en los últimos 7 días).
4. **Por módulo** (solo publicados): intentos, personas que lo intentaron, personas que lo completaron, puntaje medio de intentos y tasa de aprobación de intentos; se señalan los más difíciles (menor tasa de aprobación con al menos 3 intentos).
5. **Evaluaciones:** por perfil, enviadas, puntaje medio y tasa de aprobación; por competencia y por requisito PIMS, el % medio de aciertos (de las evaluaciones enviadas).
6. El **snapshot** para la IA es un JSON agregado: fecha, totales de participantes, estadísticas por ruta y módulo, evaluaciones, resumen del PIMS (estados), solicitudes de cambio abiertas. **Nunca** incluye nombres, emails ni identificadores de personas.
7. El **asesor** (`AnalyticsAdvisorPort`) se implementa con `agy` por subprocess: **sin shell**, prompt como un solo argumento, directorio de trabajo temporal vacío, entorno mínimo, `--sandbox`, `--mode plan`, timeout y límite de tamaño de salida. No se usa nunca `--dangerously-skip-permissions`.
8. Cada consulta (éxito o error) queda registrada: quién, pregunta, hash del snapshot, respuesta o error, duración y fecha.
9. El prompt de sistema (`docs/ai/system_prompt.md`) obliga a responder en español, usar **solo** los datos entregados, estructurar la respuesta en *Diagnóstico* y *Ajustes propuestos* (concretos por ruta o módulo) y decir cuando los datos no alcanzan.

## Criterios de aceptación
- **AC-007-1** *Given* participantes con distintos avances, *When* `GET /admin/stats/routes`, *Then* devuelve por ruta los conteos y porcentajes de la regla 3 correctos, en orden de ruta; el superadmin no se cuenta; learner → 403; sin token → 401.
- **AC-007-2** *When* `GET /admin/stats/routes/{code}`, *Then* devuelve la ruta y sus módulos publicados con intentos, puntaje medio y tasa de aprobación, y marca los más difíciles; ruta inexistente → 404.
- **AC-007-3** *When* `GET /admin/stats/assessments`, *Then* devuelve por perfil enviadas/puntaje medio/aprobación y los % por competencia y por requisito (con cláusula y título).
- **AC-007-4** *When* se construye el snapshot (`GET /admin/advisor/snapshot`), *Then* contiene rutas, módulos, evaluaciones, PIMS y solicitudes abiertas, **no contiene** ningún nombre ni email de los participantes y es determinista (mismo estado → mismo hash).
- **AC-007-5** *Given* el adaptador `agy`, *Then* invoca `[comando, "--print", prompt, …flags, "--print-timeout", "<n>s"]` sin shell, en un directorio temporal vacío, con entorno mínimo; interpreta `status = SUCCESS` y `response`; **timeout** → `AdvisorTimeout` (y mata el proceso); código de salida ≠ 0, JSON inválido o `status` ≠ SUCCESS → `AdvisorUnavailable`; trunca la respuesta a un máximo configurado.
- **AC-007-6** *When* `POST /admin/advisor/ask {question}`, *Then* 200 con la respuesta de la IA y se registra la consulta; si el asesor falla → 502 con mensaje claro y se registra como error; pregunta vacía o de más de 1 000 caracteres → 422.
- **AC-007-7** *When* `GET /admin/advisor/history`, *Then* lista las últimas consultas (máx. 50, más recientes primero) con pregunta, estado, respuesta y fecha.
- **AC-007-8** El prompt enviado contiene el prompt de sistema, el snapshot JSON y la pregunta exactamente una vez; no contiene datos personales.
- **AC-007-9** La API expone los paths/métodos de `contracts/openapi.yaml`.
- **AC-007-10** `analytics` cumple AC-001-5 (sin frameworks en `domain`/`application`).
- **AC-007-11** *Given* la UI, *Then* `/admin` muestra el panel por ruta, módulos difíciles, evaluaciones y resumen PIMS, y `/admin/advisor` permite preguntar (con preguntas de ejemplo), ver la respuesta, el historial y descargar el snapshot; un `learner` no puede acceder.
- **AC-007-12** *(manual)* Con `agy` real: la pregunta «¿Cómo están los alumnos de sensibilización?» devuelve un diagnóstico basado en los datos; se verifica en la comprobación final.

## Fuera de alcance
Gráficos interactivos avanzados, seguimiento individual de personas, aplicar automáticamente los ajustes propuestos, otra IA distinta de `agy`.
