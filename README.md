# Plataforma Capacitadora de Auditores Internos — UNSA (POC)

Capacitación en 4 rutas (Sensibilización 12 h → Interpretación 16 h → Implementación 24 h → Auditor 32 h) para formar auditores internos que conozcan la universidad. **Todos los datos son ficticios.**

- Plan completo: [PLAN.md](PLAN.md)
- Metodología: Spec-Driven Development → [specs/](specs/)
- Arquitectura: [docs/c4](docs/c4) (C1–C3) y [docs/adr](docs/adr)

## Requisitos
`uv`, Node 24+, Docker.

## Probar rápido

```bash
./dev.sh     # Postgres + migraciones + seed con cohorte demo + API (:8000) + web (:5173)
```

Abre <http://localhost:5173>. Participantes demo: `ana.quispe@demo.unsa.example` / `Demo-1234`; superadmin: las credenciales de `.env`. Guion de demo de 10 minutos: [docs/demo.md](docs/demo.md). El asesor IA necesita el CLI `agy` instalado y con sesión (sin API key).

## Puesta en marcha paso a paso

```bash
cp .env.example .env            # ajustar SUPERADMIN_EMAIL, SUPERADMIN_PASSWORD y JWT_SECRET
docker compose up -d db         # PostgreSQL 16 en el puerto 5433
```

```bash
cd backend && uv sync && uv run alembic upgrade head
```

```bash
cd backend && uv run python -m unsa_audit.seed   # BD ficticia de la UNSA + contenido de rutas + cuenta superadmin
```

> El contenido de las rutas y de los documentos institucionales vive en [content/](content/README.md). Tras editar las rutas, vuelve a ejecutar el seed. Los documentos **no se pisan** si ya existen (se conserva lo creado desde la app); para restaurarlos: `uv run python -m unsa_audit.seed --reset-documents`.

```bash
cd backend && uv run python -m unsa_audit.seed --demo         # opcional: 12 participantes demo (idempotente)
cd backend && uv run python -m unsa_audit.seed --reset-demo   # elimina @demo y @e2e y los recrea
```

```bash
cd backend && uv run unsa-audit          # API en http://localhost:8000/health
```

```bash
cd frontend && npm install && npm run dev   # UI en http://localhost:5173
```

## Verificación

```bash
cd backend && uv run ruff check . && uv run pyright && uv run pytest
```

```bash
cd frontend && npm run check && npm test && npm run build
```

Los tests de integración (`-m integration`) requieren Postgres arriba; usan una base `<POSTGRES_DB>_test` que crean y migran solos.

```bash
cd frontend && npm run test:e2e   # E2E + accesibilidad (Playwright + axe); usa Chrome del sistema y levanta API/web si no están arriba
```

## Cuentas
- **Superadmin:** el email de `SUPERADMIN_EMAIL` con la contraseña `SUPERADMIN_PASSWORD`, creada por el seed. El registro público rechaza ese email.
- **Participantes:** se registran desde `/register` (rol `learner`).
- **Participantes demo** (solo con `--demo`): `@demo.unsa.example`, contraseña documentada `Demo-1234` (dato ficticio; solo POC).
