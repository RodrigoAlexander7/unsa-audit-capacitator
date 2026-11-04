# Spec 003 — Motor de aprendizaje + Ruta 1 (Sensibilización)

**Estado:** aprobada (plan v2, Fase 2)

## Objetivo
Que un participante pueda matricularse en las rutas respetando los prerrequisitos, estudiar módulos con lectura breve + ejercicio interactivo, acumular horas y aprobar la **Ruta 1 (12 h)** completa. Los ejercicios se corrigen **en el backend** y varios se generan desde la BD ficticia de la UNSA.

## Historias
- **H1.** Como participante quiero ver las 4 rutas y cuáles puedo cursar.
- **H2.** Como participante quiero matricularme en una ruta solo si aprobé las anteriores.
- **H3.** Como participante quiero estudiar un módulo (lectura + ejercicio) y recibir retroalimentación inmediata.
- **H4.** Como participante quiero ver mis horas acreditadas y el progreso por ruta.
- **H5.** Como equipo quiero que el contenido viva en `content/` y se sincronice a la BD de forma idempotente.

## Reglas de negocio
1. Rutas secuenciales: R1 → R2 → R3 → R4. Matricularse exige haber **aprobado** (enrollment `completed`) la ruta prerrequisito.
2. Una ruta se aprueba cuando todos sus módulos obligatorios están completados (y tiene ≥ 1 módulo). Las rutas sin módulos cargados (R2–R4 hasta la Fase 5) permiten matrícula pero **nunca se completan**.
3. Un módulo con ejercicio se completa al obtener `score ≥ pass_score` (70 por defecto). Los intentos son ilimitados; se guarda el mejor puntaje. Las horas (minutos del módulo) se acreditan **una sola vez**.
4. El módulo marcado `is_final` (evaluación final) queda bloqueado hasta completar todos los demás módulos obligatorios de la ruta.
5. Para ver o resolver un módulo hay que estar matriculado en su ruta.
6. Las soluciones nunca salen del backend: la especificación pública del ejercicio no incluye respuestas, puntos ni explicaciones.
7. Tipos de ejercicio (5): `ordering`, `matching` (clasificación: cada elemento elige una categoría), `single_choice`, `quiz` (varias preguntas), `branching` (escenario con decisiones ponderadas).
8. Ejercicios **generados** desde la BD (`generator` en el contenido): `org_levels` (cargo → nivel jerárquico), `responsibility_cases` (caso → unidad responsable), `system_owners` (sistema → unidad dueña).

## Criterios de aceptación
### Catálogo y matrícula
- **AC-003-1** *Given* un usuario sin matrículas, *When* `GET /routes`, *Then* 200 con 4 rutas ordenadas (12/16/24/32 h), prerrequisitos correctos, R1 `available` y R2–R4 `locked`, y `total_hours_credited = 0`; sin token → 401.
- **AC-003-2** *Given* R1 disponible, *When* `POST /routes/sensibilizacion/enroll`, *Then* 201 con estado `in_progress`; repetirlo → 200 con la misma matrícula (idempotente).
- **AC-003-3** *Given* R1 no aprobada, *When* intento matricularme en R2 (o R4), *Then* 409 con `code = "prerequisite_not_met"`.
- **AC-003-4** *Given* una ruta inexistente, *When* `POST .../enroll` o `GET /routes/{code}`, *Then* 404.
- **AC-003-5** *Given* una matrícula en R1, *When* `GET /routes/sensibilizacion`, *Then* lista módulos (orden, título, minutos, estado `available|completed|locked`); el módulo final aparece `locked`; sin matrícula todos `locked`.

### Módulos y ejercicios
- **AC-003-6** *Given* matriculado, *When* `GET /modules/{id}`, *Then* 200 con la lección (Markdown) y la especificación **pública** del ejercicio sin claves de solución; sin matrícula → 403; módulo final bloqueado → 409; id inexistente → 404.
- **AC-003-7** *Given* cada tipo de ejercicio, *When* se corrige una respuesta, *Then* el puntaje sigue la regla del tipo (ordering: % de posiciones correctas; matching/quiz: % de aciertos; single_choice: 0/100; branching: suma de puntos / máximo) y devuelve retroalimentación por ítem.
- **AC-003-8** *Given* un módulo con ejercicio, *When* `POST /modules/{id}/attempts` con respuesta correcta, *Then* 200, `score = 100`, `passed = true`, el módulo queda `completed` y se acreditan sus minutos; con respuesta incorrecta → no se completa; con forma inválida → 422; ids desconocidos cuentan como incorrectos.
- **AC-003-9** *Given* un ejercicio generado, *When* cambia un dato de la BD (p. ej. el nombre de una unidad), *Then* la especificación pública refleja el cambio, y la respuesta correcta derivada de la BD obtiene 100.
- **AC-003-10** *Given* módulos previos incompletos, *When* intento la evaluación final, *Then* 409; con todos completos, aprobarla (≥ 70) la completa.
- **AC-003-11** *Given* todos los módulos obligatorios de R1 completados, *Then* la matrícula pasa a `completed`, `hours_credited = 12.0` y R2 pasa a `available`.
- **AC-003-12** *Given* un módulo completado, *When* reintento el ejercicio, *Then* no se acreditan horas otra vez y se conserva el mejor puntaje.
- **AC-003-13** *Given* un módulo sin ejercicio (solo lectura), *When* `POST /modules/{id}/complete`, *Then* queda completado; si el módulo tiene ejercicio → 409.
- **AC-003-14** *Given* cada intento, *Then* queda registrado (usuario, módulo, respuesta, puntaje, fecha) en `exercise_attempts` para analytics.

### Contenido
- **AC-003-15** *Given* `content/routes/`, *Then* todo el contenido es válido (kinds soportados, ids de solución existentes, generadores conocidos), los minutos de R1 suman 720 y el catálogo trae las 4 rutas con prerrequisitos coherentes.
- **AC-003-16** *Given* el seed, *When* se ejecuta dos veces, *Then* no duplica rutas/módulos y conserva los ids; un módulo quitado del contenido se elimina de la BD.

### Transversales
- **AC-003-17** La API expone todos los paths/métodos de `contracts/openapi.yaml`.
- **AC-003-18** El módulo `learning` cumple AC-001-5 (sin frameworks en `domain`/`application`).
- **AC-003-19** *Given* la UI, *When* me matriculo, abro un módulo, resuelvo el ejercicio y envío, *Then* veo mi puntaje y retroalimentación; los módulos bloqueados no son accesibles; el panel de rutas muestra estado, progreso y horas.

## Fuera de alcance
Contenido de Rutas 2–4 (Fase 5), evaluación controller/processor (Fase 5), estadísticas para el superadmin (Fase 6), componente `DiffReview` rico (Fase 3; el módulo 5 usa un `quiz` con diffs en texto), editor de contenido.

## Contenido de la Ruta 1 (12 h = 720 min, información ficticia)
| # | Módulo | Ejercicio | Min |
|---|---|---|---|
| 1 | Mapa de la UNSA | `matching` generado `org_levels` | 100 |
| 2 | Quién hace qué | `quiz` generado `responsibility_cases` | 110 |
| 3 | Normas internas | `ordering` (jerarquía documental) | 100 |
| 4 | Datos y sistemas | `matching` generado `system_owners` | 120 |
| 5 | Cambios y trazabilidad | `quiz` con diffs de ROF/procedimientos | 100 |
| 6 | Riesgos cotidianos | `branching` (3 escenarios) | 100 |
| 7 | Evaluación final | `quiz` (10 preguntas, `is_final`) | 90 |
