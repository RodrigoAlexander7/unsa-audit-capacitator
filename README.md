# Plataforma Capacitadora de Auditores Internos — UNSA (POC)

Capacitación en 4 rutas (Sensibilización 12 h → Interpretación 16 h → Implementación 24 h → Auditor 32 h) para formar auditores internos que conozcan la universidad. **Todos los datos son ficticios.**

- Plan completo: [PLAN.md](PLAN.md)
- Metodología: Spec-Driven Development → [specs/](specs/)
- Arquitectura: [docs/c4](docs/c4) (C1–C3) y [docs/adr](docs/adr)

## Requisitos
`uv`, Node 24+, Docker.

## Puesta en marcha

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

> El contenido de las rutas vive en [content/](content/README.md). Tras editarlo, vuelve a ejecutar el seed.

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

## Cuentas
- **Superadmin:** el email de `SUPERADMIN_EMAIL` con la contraseña `SUPERADMIN_PASSWORD`, creada por el seed. El registro público rechaza ese email.
- **Participantes:** se registran desde `/register` (rol `learner`).
