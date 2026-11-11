# Tasks 008 — Pulido, datos demo y cierre

- [x] T1 Solucionador de ejercicios en `seed/` (reutilizado por los tests) (AC-008-1)
- [x] T2 Seed demo: cohorte de 12 participantes + `--demo` / `--reset-demo` (AC-008-1, 3)
- [x] T3 Tests del seed demo contra las estadísticas del panel (AC-008-2, 3) — `tests/integration/test_demo_seed.py`
- [x] T4 Playwright: configuración y suite E2E (AC-008-4) — `frontend/e2e/journeys.spec.ts` (6 recorridos)
- [x] T5 axe-core en las páginas principales y correcciones (AC-008-5) — `frontend/e2e/a11y.spec.ts` (5 páginas); corregido: región con scroll del panel sin acceso por teclado
- [x] T6 `dev.sh`, README final, `docs/demo.md` (AC-008-6)
- [x] T7 Verificación con `agy` real sobre los datos demo (AC-008-7) — respuesta en ≈ 10 s que cita 11 matriculados, 4 completados, 3 estancados, 92 % de aprobación y los módulos 4, 6 y 7 como difíciles
- [x] T8 Docs finales (PLAN, C4), memoria y commit único de la fase

## Notas de cierre
- Las pruebas E2E esperan a `networkidle` tras `goto`: sin ello la hidratación de Svelte puede borrar lo escrito en campos controlados.
- Las pruebas E2E crean cuentas `@e2e.unsa.example`; `--reset-demo` las elimina.
- E2E usa el Chrome del sistema (`channel: 'chrome'`); no descarga navegadores.
