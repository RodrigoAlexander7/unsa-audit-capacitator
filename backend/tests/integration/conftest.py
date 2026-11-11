"""Fixtures de integracion: BD `<db>_test` migrada con Alembic y limpiada por test."""

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any
from uuid import UUID

import asyncpg
import httpx
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import make_url

from tests.solutions import solve
from unsa_audit.core.config import Settings, get_settings
from unsa_audit.learning.application.generators import generate_spec
from unsa_audit.learning.infrastructure.sqlalchemy_repository import SqlAlchemyLearningRepository
from unsa_audit.learning.infrastructure.sqlalchemy_university_facts import (
    SqlAlchemyUniversityFacts,
)
from unsa_audit.main import create_app
from unsa_audit.seed.loader import (
    ensure_superadmin,
    load_university,
    sync_content,
    sync_documents,
)

BACKEND_DIR = Path(__file__).resolve().parents[2]
SUPERADMIN_EMAIL = "superadmin@test.example"
SUPERADMIN_PASSWORD = "superadmin-test-pass"

_TABLES = (
    "change_requests, document_versions, documents, "
    "exercise_attempts, module_progress, enrollments, modules, routes, "
    "users, data_owners, processing_activities, systems, people, positions, org_units"
)


def _test_database_url() -> str:
    url = make_url(get_settings().database_url)
    return url.set(database=f"{url.database}_test").render_as_string(hide_password=False)


async def _ensure_database(url: str) -> None:
    parsed = make_url(url)
    conn = await asyncpg.connect(
        host=parsed.host,
        port=parsed.port,
        user=parsed.username,
        password=parsed.password,
        database="postgres",
    )
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", parsed.database
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{parsed.database}"')
    finally:
        await conn.close()


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    url = _test_database_url()
    asyncio.run(_ensure_database(url))
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.attributes["url"] = url
    command.upgrade(cfg, "head")
    return Settings(  # pyright: ignore[reportCallIssue]
        _env_file=None,  # pyright: ignore[reportCallIssue]
        database_url=url,
        superadmin_email=SUPERADMIN_EMAIL,
        superadmin_password=SUPERADMIN_PASSWORD,
        jwt_secret="t" * 32,
    )


@pytest.fixture
async def app(test_settings: Settings) -> AsyncIterator:
    application = create_app(test_settings)
    async with application.state.engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {_TABLES} CASCADE"))
    yield application
    await application.state.engine.dispose()


@pytest.fixture
async def client(app) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


async def register_and_login(
    client: httpx.AsyncClient, email: str = "ana@example.com", password: str = "password123"
) -> dict[str, str]:
    """Registra un learner y devuelve cabeceras Authorization listas para usar."""
    response = await client.post(
        "/auth/register", json={"email": email, "password": password, "full_name": "Ana Quispe"}
    )
    assert response.status_code == 201, response.text
    login = await client.post("/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.fixture
async def seeded(app):
    """App con la BD ficticia de la UNSA, el contenido de las rutas y los documentos cargados."""
    await load_university(app.state.session_factory)
    await sync_content(app.state.session_factory, app.state.settings)
    await sync_documents(app.state.session_factory, app.state.settings)
    return app


async def solve_module(app, module_id: str) -> dict[str, Any]:
    """Respuesta perfecta para el ejercicio de un modulo (lee la spec privada de la BD)."""
    repo = SqlAlchemyLearningRepository(app.state.session_factory)
    module = await repo.get_module(UUID(module_id))
    assert module is not None and module.exercise is not None
    ex = module.exercise
    if ex.generator:
        facts = await SqlAlchemyUniversityFacts(app.state.session_factory).snapshot()
        spec = generate_spec(ex.generator, ex.params, facts)
    else:
        spec = ex.spec
    return solve(ex.kind, spec)


async def superadmin_headers(client: httpx.AsyncClient, app) -> dict[str, str]:
    """Crea la cuenta superadmin como lo hace el seed y devuelve sus cabeceras."""
    await ensure_superadmin(app.state.session_factory, app.state.settings)
    login = await client.post(
        "/auth/login", json={"email": SUPERADMIN_EMAIL, "password": SUPERADMIN_PASSWORD}
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}
