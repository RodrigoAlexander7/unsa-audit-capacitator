# Tasks 001 — Fundaciones

- [x] T1 `.gitignore`, `.env.example`, `README.md` (AC-001-1, 4)
- [x] T2 `docker-compose.yml` con Postgres 16 + healthcheck, puerto 5433 (AC-001-1)
- [x] T3 Backend: `uv init`, dependencias, layout de paquetes (AC-001-9)
- [x] T4 `Settings` con config obligatoria + test (AC-001-4)
- [x] T5 Caso de uso `CheckHealth` + puerto + adaptador + router + tests (AC-001-3)
- [x] T6 Alembic configurado y migración 0001 (AC-001-2)
- [x] T7 Test de arquitectura por imports (AC-001-5)
- [x] T8 Frontend `sv create`, tema claro fijo, página inicial con estado API + marca POC (AC-001-6, 7)
- [x] T9 ADR-001..003 (AC-001-8)
- [x] T10 C4 C1, C2, C3 en `docs/c4/` (AC-001-8)
- [x] T11 Verificación completa: ruff, pyright, pytest (8 pass, incl. integración con Postgres real), svelte-check, vitest (3 pass), build frontend, `/health` y SSR de la home contra el API real (AC-001-9)

## Notas de cierre
- SvelteKit 3 cambió el manejo de env: se usa `src/env.ts` con `defineEnvVars` y `$app/env/private` (variable `API_URL`).
- Frontend sin test del tema oscuro automatizado (AC-001-7 verificado por inspección: `color-scheme: light` fijo en `app.html` y `app.css`, sin `prefers-color-scheme`).
