# Spec 001 — Fundaciones

**Estado:** aprobada (plan v2, Fase 0)

## Objetivo
Dejar el repositorio listo para construir las siguientes fases: estructura monorepo, backend FastAPI con Clean Architecture, frontend SvelteKit (solo tema claro), PostgreSQL por Docker, migraciones, configuración por entorno, documentación C4 y ADRs.

## Historias
- **H1.** Como desarrollador quiero levantar todo el entorno con pocos comandos documentados para empezar a trabajar rápido.
- **H2.** Como desarrollador quiero un backend con estructura por capas y un endpoint de salud para validar la composición.
- **H3.** Como desarrollador quiero un frontend que consuma ese endpoint para validar la integración end-to-end.
- **H4.** Como revisor quiero documentación de arquitectura (C1–C3) y decisiones (ADR) en el repo.

## Criterios de aceptación
- **AC-001-1** *Given* el repo clonado y `.env` creado desde `.env.example`, *When* ejecuto `docker compose up -d db`, *Then* PostgreSQL 16 acepta conexiones en el puerto configurado y el healthcheck pasa.
- **AC-001-2** *Given* Postgres arriba, *When* ejecuto `uv run alembic upgrade head`, *Then* la migración inicial se aplica sin error.
- **AC-001-3** *Given* el backend arrancado, *When* hago `GET /health`, *Then* responde `200` con `{"status":"ok","database":"up"}` si la BD responde, y `503` con `"database":"down"` si no.
- **AC-001-4** *Given* `SUPERADMIN_EMAIL` no definido, *When* arranca el backend, *Then* falla con un error de configuración claro (config obligatoria).
- **AC-001-5** *Given* el código del backend, *When* se ejecuta el test de arquitectura, *Then* `domain` y `application` no importan `fastapi`, `sqlalchemy` ni `subprocess`.
- **AC-001-6** *Given* backend y frontend arrancados, *When* abro la página de inicio, *Then* muestra el estado del API leído de `/health` y la marca "Datos ficticios – POC".
- **AC-001-7** *Given* el frontend, *When* inspecciono estilos, *Then* no existe tema oscuro (`color-scheme: light` fijo).
- **AC-001-8** *Given* el repo, *When* reviso `docs/`, *Then* existen C1, C2 y C3 (Mermaid) y ADR-001..003.
- **AC-001-9** *Given* el repo, *When* ejecuto lint/tipos/tests de backend y frontend, *Then* todos pasan.

## Fuera de alcance
Autenticación, modelo de dominio, contenido, IA (fases siguientes).

## Preguntas resueltas
- Puerto 5432 del host está ocupado → Postgres de Docker se publica en **5433** (configurable con `POSTGRES_PORT`).
