# Plan 003 — Motor de aprendizaje + Ruta 1

## Módulo `learning` (Clean Architecture)
**domain**
- `route.py`: `Route`, `Module`, `ExerciseDef`, `Enrollment`, `ModuleProgress`, enums (`ExerciseKind`, `EnrollmentStatus`, `ModuleStatus`, `RouteStatus`).
- `exercises.py`: `validate_spec`, `to_public` (quita soluciones, baraja de forma determinista), `grade` por tipo → `GradeResult`; errores `InvalidAnswer`, `InvalidExerciseSpec`.
- `progress.py`: funciones puras `module_status`, `route_completed`, `route_status`, `credited_minutes`.

**application**
- `ports.py`: `LearningRepository`, `UniversityFacts` (hechos de la UNSA que alimentan generadores: unidades, cargos, sistemas), `ContentSource`.
- `generators.py`: `org_levels`, `responsibility_cases`, `system_owners` (funciones puras sobre los hechos).
- `use_cases.py`: `ListRoutes`, `GetRoute`, `EnrollInRoute`, `GetModule`, `SubmitAttempt`, `CompleteReadingModule`, `SyncContent`.

**infrastructure**
- `models.py` (ORM), `sqlalchemy_repository.py`, `sqlalchemy_university_facts.py`, `content_loader.py` (lee `content/routes/**`).

**interface**: `router.py` con schemas; errores de dominio → HTTP (404/403/409/422).

## Decisiones
- **Un ejercicio por módulo** (columnas en `modules`), en vez de una tabla `exercises` aparte (el PLAN §6 la preveía). Se reevalúa en F5 si un módulo necesita varios.
- **Contenido** en `content/routes/<codigo>/`: `route.yaml` (metadatos), `NN-slug.md` (frontmatter YAML + lección Markdown) y `NN-slug.exercise.json`. `pyyaml` pasa a dependencia de runtime.
- **Sincronización** `SyncContent` (upsert + borrado de módulos retirados) se ejecuta desde el seed. Ids de módulo deterministas (`uuid5(route:slug)`).
- **Generadores** se evalúan al pedir el módulo y otra vez al corregir (determinista: ordenan por nombre y barajan con semilla del módulo). Si la BD cambia entre ambos pasos, los ids desconocidos cuentan como incorrectos.
- **Final**: `is_final` en el frontmatter bloquea el módulo hasta completar los demás obligatorios.
- **Rutas 2–4**: solo `route.yaml` (sin módulos) → matrícula permitida pero nunca se completan hasta F5.
- **Lecciones Markdown** se renderizan con `marked` en el servidor SvelteKit; el contenido es del repositorio (confiable).

## Datos (migración 0003)
`routes`, `modules` (JSONB para spec/params), `enrollments`, `module_progress`, `exercise_attempts` (FK con `ON DELETE CASCADE` hacia `modules`).

## Frontend
`/routes` (panel), `/routes/[code]` (módulos), `/routes/[code]/[module]` (lección + ejercicio). Componentes en `src/lib/exercises/`: `Ordering`, `Matching`, `SingleChoice`, `Quiz`, `Branching` y `ExerciseForm`. Ordenar con botones ↑/↓ (accesible, sin dependencias). El envío pasa por una *form action* (el JWT es `httpOnly`).

## Tests
- Unit: graders (5 tipos), `to_public` sin soluciones, progreso/gating, generadores, casos de uso con repositorio en memoria, validez de todo `content/`.
- Integración (Postgres real): flujo completo de R1 hasta 12 h y desbloqueo de R2, gating, 403/409/422, idempotencia del sync, contrato.
