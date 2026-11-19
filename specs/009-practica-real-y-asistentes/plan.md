# Plan 009+ — Práctica con documentos reales y asistentes IA

**Estado:** propuesta para aprobación (no implementada). Continúa el PLAN.md v2 (F0–F7 hechas).

## Objetivo
1. **Práctica seria con las plantillas reales** (`raw/files/`, toolkit ISO 27001 → adaptado a 27701): cada módulo de las Rutas 2–4 trae un **ejemplo resuelto** (documento de la UNSA ficticia ya completado) y un **ejercicio donde el participante completa el documento**, con corrección rigurosa en backend. Se completan **todos** los módulos de las 3 rutas (hoy casi todos son `planned`).
2. **Asistente flotante del estudiante**: popup siempre disponible que explica los temas del módulo actual y conoce la UNSA; no revela soluciones.
3. **Asistente flotante del administrador**: el mismo popup en modo admin para consultar el avance de los estudiantes y proponer reestructuraciones del plan.

## Dos pistas (independientes, pueden ir en sesiones paralelas)

| Pista | Toca | Fases |
|---|---|---|
| **A — Contenido y práctica** | `learning`, `content/`, `seed/solutions.py`, `seed/demo.py`, frontend `lib/exercises` | F8 → F9 → F10 → F11 |
| **B — Asistentes IA** | módulo nuevo `assistant`, `analytics`, `frontend` layout + componente popup | F12 → F13 |

Regla del repo: una fase a la vez, **un commit por fase**, aprobación entre fases.

## Fases

| Fase | Spec | Contenido | Entregable verificable |
|---|---|---|---|
| **F8 — Motor de práctica documental** | 009 | Inventario estructural de las 16 plantillas (`docs/practica-documental/inventario-plantillas.md`, solo estructura, sin copiar texto). Nuevos tipos de ejercicio con corrección determinista: `document_form` (campos tipados + reglas entre campos), `risk_table` (activo/amenaza/vulnerabilidad/valoración → riesgo calculado), `treatment_table`, `audit_checklist`, `nonconformity_form`, `competence_matrix`. Formato de autoría, vista de «ejemplo resuelto» junto al formulario, extensión del solucionador del seed. | Un ejercicio de cada tipo funcional, con tests unitarios de corrección y E2E de un formulario. |
| **F9 — Ruta 2 completa (16 h)** | 010 | Los 8 módulos desarrollados (alcance, política, riesgos, controles/SoA, controller/processor, requisito→documento, competencia/monitoreo, evaluación). | Ruta 2 sin módulos `planned`; horas = 16 h; completable de punta a punta. |
| **F10 — Ruta 3 completa (24 h)** | 011 | Los 9 módulos: brecha, inventario, evaluación de riesgos (Cuadro xlsx), SoA, políticas/procedimientos, plan de tratamiento, evidencias, indicadores, evaluación. | Ruta 3 completa; horas = 24 h. |
| **F11 — Ruta 4 completa (32 h)** | 012 | Los 10 módulos: principios, programa anual, plan y criterios, listas de verificación, entrevistas/evidencia, simulación, hallazgos/medidas correctivas, informe, competencia, evaluación. | Ruta 4 completa; horas = 32 h. Demo seed y analytics/E2E actualizados. |
| **F12 — Asistente del estudiante** | 013 | Módulo `assistant` (puerto + adaptador `agy`), recuperación de contexto (lección actual + documentos institucionales + hechos de la UNSA), popup flotante accesible en todas las páginas, historial por usuario, límites, protección contra *prompt injection* y contra filtración de soluciones. | Pregunta sobre el módulo actual responde con contenido de la UNSA y no entrega respuestas de ejercicios (test). |
| **F13 — Asistente del admin + reestructuración** | 014 | Modo admin del popup: consultas sobre avance (agregado y por alias seudónimo), propuestas estructuradas de reestructuración (qué módulo, qué cambio, por qué, evidencia) guardadas como borradores revisables. | «¿Qué módulos reestructurarías?» devuelve propuestas con cifras; la UI resuelve alias→nombre **localmente**. |

## Decisiones ya tomadas (heredadas)
- Corrección **siempre en backend**, la spec pública no lleva soluciones.
- IA vía `agy` por subprocess (ADR-003), sin API key; nada de PII hacia `agy`.
- Contenido propio: **no se copian textos** de `raw/` ni se versiona `raw/` (autor acreditado).
- Clean Architecture + SDD (spec → tests → código), ACs con `@pytest.mark.ac`.

## Decisiones abiertas (recomendación entre paréntesis)
1. ¿Seguir siendo 100 % determinista la corrección de textos libres? (Sí: criterios por palabras clave/estructura; la IA solo da retroalimentación opcional, nunca nota.)
2. ¿Consultas por estudiante del admin? (Alias seudónimo estable `P-07`; la tabla alias→persona vive solo en el backend y se resuelve en la UI.)
3. ¿Historial del asistente persistente? (Sí, por usuario, con borrado; el admin no ve conversaciones de estudiantes.)
4. ¿Confirmar licencia del toolkit antes de publicar el repo? (Pendiente, ya anotado en `docs/adaptacion-plantillas-27001-a-27701.md`.)
