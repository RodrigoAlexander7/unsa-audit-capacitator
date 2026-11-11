import httpx
import pytest
from sqlalchemy import text

from tests.integration.conftest import (
    SUPERADMIN_EMAIL,
    SUPERADMIN_PASSWORD,
    register_and_login,
    superadmin_headers,
)
from unsa_audit.seed.loader import ensure_superadmin

pytestmark = pytest.mark.integration


@pytest.mark.ac("AC-002-1")
async def test_registro_devuelve_learner_sin_secretos(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/auth/register",
        json={"email": "Ana@Example.com", "password": "password123", "full_name": "Ana Quispe"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["role"] == "learner"
    assert body["email"] == "ana@example.com"
    assert not {"password", "password_hash"} & body.keys()


@pytest.mark.ac("AC-002-2")
async def test_registro_duplicado_409(client: httpx.AsyncClient) -> None:
    payload = {"email": "ana@example.com", "password": "password123", "full_name": "Ana"}
    assert (await client.post("/auth/register", json=payload)).status_code == 201
    duplicate = await client.post("/auth/register", json={**payload, "email": "ANA@example.com"})
    assert duplicate.status_code == 409


@pytest.mark.ac("AC-002-3")
async def test_no_se_puede_registrar_el_email_superadmin(client: httpx.AsyncClient) -> None:
    attempt = await client.post(
        "/auth/register",
        json={"email": SUPERADMIN_EMAIL, "password": "password123", "full_name": "Intruso"},
    )
    assert attempt.status_code == 409
    taken = await client.post(
        "/auth/register",
        json={"email": "ana@example.com", "password": "password123", "full_name": "Ana"},
    )
    again = await client.post(
        "/auth/register",
        json={"email": "ana@example.com", "password": "password123", "full_name": "Ana"},
    )
    assert taken.status_code == 201
    assert attempt.json() == again.json(), "mismo mensaje que un email duplicado"


@pytest.mark.ac("AC-002-4")
@pytest.mark.parametrize(
    "payload",
    [
        {"email": "ana@example.com", "password": "corta", "full_name": "Ana"},
        {"email": "sin-arroba", "password": "password123", "full_name": "Ana"},
        {"email": "ana@example.com", "password": "password123", "full_name": ""},
    ],
)
async def test_registro_invalido_422(client: httpx.AsyncClient, payload: dict) -> None:
    assert (await client.post("/auth/register", json=payload)).status_code == 422


@pytest.mark.ac("AC-002-5")
async def test_login_ok_y_errores_genericos(client: httpx.AsyncClient) -> None:
    await register_and_login(client)
    ok = await client.post(
        "/auth/login", json={"email": "ana@example.com", "password": "password123"}
    )
    assert ok.status_code == 200
    assert ok.json()["token_type"] == "bearer"
    assert ok.json()["user"]["role"] == "learner"

    bad_password = await client.post(
        "/auth/login", json={"email": "ana@example.com", "password": "incorrecta"}
    )
    unknown = await client.post(
        "/auth/login", json={"email": "nadie@example.com", "password": "password123"}
    )
    assert bad_password.status_code == unknown.status_code == 401
    assert bad_password.json() == unknown.json()


@pytest.mark.ac("AC-002-6")
async def test_me_con_y_sin_token(client: httpx.AsyncClient) -> None:
    headers = await register_and_login(client)
    me = await client.get("/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "ana@example.com"

    assert (await client.get("/me")).status_code == 401
    assert (await client.get("/me", headers={"Authorization": "Bearer basura"})).status_code == 401


@pytest.mark.ac("AC-002-7")
async def test_seed_superadmin_idempotente_y_puede_iniciar_sesion(
    client: httpx.AsyncClient, app
) -> None:
    await ensure_superadmin(app.state.session_factory, app.state.settings)
    await ensure_superadmin(app.state.session_factory, app.state.settings)
    async with app.state.engine.connect() as conn:
        count = await conn.scalar(
            text("SELECT count(*) FROM users WHERE email = :e"), {"e": SUPERADMIN_EMAIL}
        )
    assert count == 1
    login = await client.post(
        "/auth/login", json={"email": SUPERADMIN_EMAIL, "password": SUPERADMIN_PASSWORD}
    )
    assert login.status_code == 200
    assert login.json()["user"]["role"] == "superadmin"


@pytest.mark.ac("AC-002-8")
async def test_admin_ping_segun_rol(client: httpx.AsyncClient, app) -> None:
    assert (await client.get("/admin/ping")).status_code == 401
    learner = await register_and_login(client)
    assert (await client.get("/admin/ping", headers=learner)).status_code == 403
    admin = await superadmin_headers(client, app)
    assert (await client.get("/admin/ping", headers=admin)).status_code == 200


@pytest.mark.ac("AC-002-9")
async def test_password_almacenado_como_argon2(client: httpx.AsyncClient, app) -> None:
    await register_and_login(client)
    async with app.state.engine.connect() as conn:
        stored = await conn.scalar(
            text("SELECT password_hash FROM users WHERE email = 'ana@example.com'")
        )
    assert stored.startswith("$argon2")
    assert "password123" not in stored
