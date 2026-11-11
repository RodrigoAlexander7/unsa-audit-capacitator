# Tasks 003 — Motor de aprendizaje + Ruta 1

- [x] T1 Contrato `contracts/openapi.yaml` (AC-003-17)
- [x] T2 domain: entidades, `exercises.py` (validate/to_public/grade), `progress.py` + unit tests (AC-003-6, 7, 11)
- [x] T3 application: puertos, generadores, casos de uso + unit tests con fakes (AC-003-2, 3, 8, 9, 10, 12, 13)
- [x] T4 infrastructure: ORM, repositorio, hechos UNSA, content loader (AC-003-14, 15, 16)
- [x] T5 migración 0003 (autogenerate revisado)
- [x] T6 Contenido Ruta 1 (7 módulos) y `route.yaml` de las 4 rutas (AC-003-15)
- [x] T7 interface: router, schemas, mapeo de errores, wiring en `main.py` (AC-003-1..6, 8)
- [x] T8 seed: `SyncContent` en `seed_all` + comando (AC-003-16)
- [x] T9 tests de integración (flujo R1 completo, gating, contrato) (AC-003-1..14, 17)
- [x] T10 Frontend: panel de rutas, módulos, lección, 5 componentes de ejercicio (AC-003-19)
- [x] T11 Verificación completa, docs (README/C4/PLAN) y commit único de la fase (AC-003-18)

## Notas de cierre
- Verificado: ruff, pyright, 118 tests backend (82 unit + 36 integración con Postgres real), svelte-check, 12 vitest y build.
- AC-003-19 verificado manualmente en el navegador integrado: panel `/routes`, matrícula, ruta con 7 módulos (final bloqueado), ejercicio `ordering` armado con ↑/↓ y enviado (100 % aprobado, intento persistido), ejercicio `matching` generado desde la BD con botón de envío deshabilitado hasta responder todo. Los demás tipos (`quiz`, `branching`, `single_choice`) están cubiertos por tests de backend y por la lógica `completion/canSubmit` del frontend, pero no se recorrieron uno a uno en la UI. Sin E2E automatizado (llega con Playwright en F7).
- Ruta 1 completa recorrida de punta a punta por la API en `test_completar_la_ruta_1_acredita_12_horas_y_desbloquea_la_ruta_2` (12.0 h, R2 disponible).
- Los minutos del contenido son "dedicación estimada" (lectura + práctica + reflexión), no tiempo de pantalla.
- `quiz` y `single_choice` devuelven la explicación (que revela la respuesta) tras cada intento; `ordering` y `matching` no revelan la solución. Si se quiere endurecer, basta quitar `explanation` del contenido.
- Pendiente para fases siguientes: `DiffReview` rico (F3), contenido de Rutas 2–4 (F5), analytics (F6).
