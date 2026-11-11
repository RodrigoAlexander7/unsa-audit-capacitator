import httpx
import pytest
from sqlalchemy import text

from tests.integration.conftest import register_and_login, superadmin_headers
from unsa_audit.seed.demo import COHORT, DEMO_PASSWORD, seed_demo

pytestmark = pytest.mark.integration


async def _count_users(app) -> int:
    async with app.state.session_factory() as session:
        return (await session.execute(text("SELECT count(*) FROM users"))).scalar_one()


@pytest.mark.ac("AC-008-1")
async def test_seed_demo_crea_el_cohorte_y_es_idempotente(
    client: httpx.AsyncClient, seeded
) -> None:
    first = await seed_demo(seeded.state.session_factory, seeded.state.settings)
    assert (first.created, first.skipped, first.removed) == (12, 0, 0)

    second = await seed_demo(seeded.state.session_factory, seeded.state.settings)
    assert (second.created, second.skipped) == (0, 12)
    assert await _count_users(seeded) == 12

    # La contraseña documentada permite iniciar sesión.
    login = await client.post(
        "/auth/login", json={"email": COHORT[0].email, "password": DEMO_PASSWORD}
    )
    assert login.status_code == 200
    routes = await client.get(
        "/routes", headers={"Authorization": f"Bearer {login.json()['access_token']}"}
    )
    codes = {r["code"]: r for r in routes.json()["routes"]}
    assert codes["sensibilizacion"]["status"] == "completed"
    assert codes["implementacion"]["status"] == "completed"


@pytest.mark.ac("AC-008-2")
async def test_estadisticas_del_panel_con_el_cohorte_demo(
    client: httpx.AsyncClient, seeded
) -> None:
    await seed_demo(seeded.state.session_factory, seeded.state.settings)
    admin = await superadmin_headers(client, seeded)

    routes = {r["code"]: r for r in (await client.get("/admin/stats/routes", headers=admin)).json()}
    r1, r2, r3 = routes["sensibilizacion"], routes["interpretacion"], routes["implementacion"]
    assert r1["enrolled"] >= 10 and r1["completed"] >= 3
    assert r2["completed"] >= 1 and r3["completed"] >= 1
    assert r1["stalled"] >= 2

    detail = (await client.get("/admin/stats/routes/sensibilizacion", headers=admin)).json()
    assert any(m["hardest"] for m in detail["modules"]), "debe haber algún módulo difícil"

    assessments = (await client.get("/admin/stats/assessments", headers=admin)).json()
    profiles = {a["profile"]: a for a in assessments}
    assert set(profiles) == {"controller", "processor"}
    assert all(a["competencies"] for a in profiles.values())

    snapshot = str((await client.get("/admin/advisor/snapshot", headers=admin)).json())
    assert "@" not in snapshot, "el snapshot no debe contener correos"
    for learner in COHORT:
        assert learner.name not in snapshot, learner.name


@pytest.mark.ac("AC-008-3")
async def test_reset_demo_solo_toca_cuentas_demo_y_e2e(client: httpx.AsyncClient, seeded) -> None:
    factory, settings = seeded.state.session_factory, seeded.state.settings
    await seed_demo(factory, settings)
    await register_and_login(client, "e2e-1@e2e.unsa.example")
    await register_and_login(client, "otra.persona@example.com")
    await superadmin_headers(client, seeded)
    before = await _count_users(seeded)
    assert before == 12 + 3

    result = await seed_demo(factory, settings, reset=True)
    assert (result.removed, result.created) == (13, 12)  # 12 demo + 1 e2e
    assert await _count_users(seeded) == 12 + 2  # quedan: otra persona y superadmin

    async with factory() as session:
        emails = set((await session.execute(text("SELECT email FROM users"))).scalars())
    assert {"otra.persona@example.com", settings.superadmin_email} <= emails
    assert "e2e-1@e2e.unsa.example" not in emails
