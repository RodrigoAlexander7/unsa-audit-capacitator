# Plan 002 — Identity + University

## Módulos (cada uno con `domain / application / infrastructure / interface`)
**identity**
- domain: `User`, `Role(learner|superadmin)`, `normalize_email`.
- application: puertos `UserRepository`, `PasswordHasher`, `TokenService`; casos de uso `RegisterUser`, `Login`, `GetCurrentUser`, `EnsureSuperadmin`.
- infrastructure: `SqlAlchemyUserRepository` (+ ORM `UserModel`), `Argon2PasswordHasher`, `JwtTokenService` (HS256, expiración desde `JWT_EXPIRE_MINUTES`).
- interface: routers `/auth/register`, `/auth/login`, `/me`, `/admin/ping`; dependencias `current_user`, `require_superadmin`.

**university**
- domain: `OrgUnit`, `OrgUnitKind`, `Position`, `Person`, `PersonKind`, `System`, `DataOwner`, `DataOwnerRole`, `ProcessingActivity` + función pura `build_org_tree`.
- application: puerto de lectura `UniversityReadRepository`; casos de uso `GetOrgTree`, `GetOrgUnitDetail`, `ListSystems`.
- infrastructure: modelos ORM, `SqlAlchemyUniversityReadRepository`.
- interface: `/org-units`, `/org-units/{id}`, `/systems` (requieren usuario autenticado).

## Persistencia
- `core/database.py` expone `Base` (DeclarativeBase). Alembic importa los modelos de cada módulo.
- Migración `0002`: `users`, `org_units`, `positions`, `people`, `systems`, `data_owners`, `processing_activities` (UUID como PK).
- `alembic/env.py` acepta URL por `config.attributes["url"]` (usado por los tests con BD `<db>_test`).

## Seed
- `unsa_audit.seed` (`uv run python -m unsa_audit.seed`): datos en `seed/university_data.py` con UUID determinista (`uuid5(slug)`), carga idempotente (borra y recarga solo tablas university) + `EnsureSuperadmin`.
- Config nueva: `SUPERADMIN_PASSWORD` (solo para seed).

## Tests
- Unit con fakes: `RegisterUser`, `Login`, `GetCurrentUser`, `EnsureSuperadmin`, JWT, `build_org_tree`.
- Integración sobre Postgres real, BD `<db>_test` creada y migrada por fixture de sesión; tablas limpiadas por test.
- Contrato: `tests/integration/test_contract.py` compara `app.openapi()` con `contracts/openapi.yaml`.

## Frontend
- `hooks.server.ts`: cookie `httpOnly` `token` → `GET /me` → `locals.user`.
- Rutas: `/login`, `/register`, `/logout` (action), `/university` (protegida). `lib/api.ts` envoltorio tipado.
