# Tasks 002 — Identity + University

- [x] T1 Contrato `contracts/openapi.yaml` (AC-002-14)
- [x] T2 Config `SUPERADMIN_PASSWORD`, `Base` ORM, `env.py` con URL inyectable
- [x] T3 identity/domain + application (+ unit tests) (AC-002-1..6, 8)
- [x] T4 identity/infrastructure (Argon2, JWT, repo SQLAlchemy) (AC-002-5, 6, 9)
- [x] T5 identity/interface (routers, dependencias, `/admin/ping`) (AC-002-1..6, 8)
- [x] T6 university/domain + application + `build_org_tree` (+ unit tests)
- [x] T7 university infrastructure + interface (AC-002-11..13)
- [x] T8 Migración 0002 (autogenerate revisado)
- [x] T9 Seed ficticio + `EnsureSuperadmin` + comando (AC-002-7, 10)
- [x] T10 Fixtures de integración (BD `<db>_test`) + tests de integración + contrato (AC-002-14)
- [x] T11 Frontend: hooks, login, registro, logout, `/university`, `/university/[id]`, `/systems` (AC-002-16)
- [x] T12 Verificación completa y actualización de README/C4 (AC-002-15)

## Notas de cierre
- Verificado: ruff, pyright, 43 tests backend (unit + integración con Postgres real), svelte-check, 7 tests vitest, build.
- AC-002-16 verificado manualmente: registro → sesión → `/university` → `/systems` → logout con curl contra el SSR, y login del superadmin desde el navegador integrado. La cookie `token` es `httpOnly`. Sin test E2E automatizado (llega con Playwright en F7).
- `frontend/.prettierrc` fija el estilo (tabs, comillas simples) para que `prettier` no reformatee el proyecto.
- `/admin/ping` existe solo para demostrar el control de rol; el panel real llega en F6.
- Pendiente para fases siguientes: vincular `users` ↔ `people`, endpoint de `processing_activities`.
