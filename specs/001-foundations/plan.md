# Plan 001 — Fundaciones

## Decisiones técnicas
- **Backend:** Python 3.12, `uv`, FastAPI, SQLAlchemy 2 (async) + asyncpg, Alembic, pydantic-settings. Layout `src/unsa_audit/`.
- **Capas:** `shared/` (kernel), `platform/` (config, db, health). Los módulos de negocio (`identity`, `university`, …) llegan en fases siguientes con `{domain,application,infrastructure,interface}`.
- **Health:** caso de uso `CheckHealth` (application) con puerto `DatabaseProbe`; adaptador SQLAlchemy en infrastructure; router en interface.
- **Config:** `Settings` (pydantic-settings) lee `.env`; `SUPERADMIN_EMAIL`, `DATABASE_URL`, `JWT_SECRET` obligatorios.
- **Frontend:** SvelteKit + TypeScript, adapter-auto; CSS propio con variables, `color-scheme: light`. Proxy a la API en dev vía `VITE_API_URL`/`+page.server.ts`.
- **BD:** Postgres 16 en docker-compose, puerto host 5433, volumen nombrado, healthcheck `pg_isready`.
- **Tests:** pytest (unit para `CheckHealth` con fake; arquitectura con análisis de imports AST), vitest para frontend.
- **Docs:** C4 en Mermaid (`docs/c4/*.md`), ADRs en `docs/adr/`.

## Estructura creada
```
backend/src/unsa_audit/{main.py, shared/, platform/{config,database}.py, health/{application,infrastructure,interface}}
backend/alembic/ (migración 0001 vacía/base)
backend/tests/{unit,integration}/
frontend/ (sv create minimal)
docker-compose.yml  .env.example  .gitignore  README.md
docs/{c4,adr,ai}/
```
