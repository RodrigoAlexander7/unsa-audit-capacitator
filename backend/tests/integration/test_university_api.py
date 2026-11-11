import httpx
import pytest
from sqlalchemy import text

from tests.integration.conftest import register_and_login
from unsa_audit.seed.loader import load_university

pytestmark = pytest.mark.integration


def _flatten(node: dict) -> list[dict]:
    return [node, *(d for child in node["children"] for d in _flatten(child))]


async def _counts(app) -> dict[str, int]:
    tables = ["org_units", "positions", "people", "systems", "data_owners", "processing_activities"]
    async with app.state.engine.connect() as conn:
        return {t: await conn.scalar(text(f"SELECT count(*) FROM {t}")) for t in tables}


@pytest.mark.ac("AC-002-10")
async def test_seed_carga_cantidades_y_es_idempotente(app) -> None:
    await load_university(app.state.session_factory)
    first = await _counts(app)
    await load_university(app.state.session_factory)
    assert await _counts(app) == first
    assert first["org_units"] >= 25
    assert first["people"] >= 60
    assert first["systems"] == 8
    assert first["processing_activities"] == 10


@pytest.mark.ac("AC-002-11")
async def test_org_units_devuelve_arbol_con_raiz_rectorado(client: httpx.AsyncClient, app) -> None:
    await load_university(app.state.session_factory)
    headers = await register_and_login(client)
    response = await client.get("/org-units", headers=headers)
    assert response.status_code == 200
    root = response.json()
    assert root["kind"] == "rectorado"
    kinds = [n["kind"] for n in _flatten(root)]
    assert kinds.count("facultad") == 4
    assert kinds.count("escuela") == 12
    vr = next(c for c in root["children"] if c["name"] == "Vicerrectorado Académico")
    assert {c["kind"] for c in vr["children"]} == {"facultad", "oficina"}


@pytest.mark.ac("AC-002-11")
async def test_org_units_requiere_autenticacion(client: httpx.AsyncClient, app) -> None:
    await load_university(app.state.session_factory)
    assert (await client.get("/org-units")).status_code == 401


@pytest.mark.ac("AC-002-11")
async def test_org_units_404_si_no_hay_seed(client: httpx.AsyncClient) -> None:
    headers = await register_and_login(client)
    assert (await client.get("/org-units", headers=headers)).status_code == 404


@pytest.mark.ac("AC-002-12")
async def test_detalle_de_unidad_con_cargos_y_titulares(client: httpx.AsyncClient, app) -> None:
    await load_university(app.state.session_factory)
    headers = await register_and_login(client)
    tree = (await client.get("/org-units", headers=headers)).json()
    oti = next(n for n in _flatten(tree) if n["code"] == "OTI")

    response = await client.get(f"/org-units/{oti['id']}", headers=headers)
    assert response.status_code == 200
    detail = response.json()
    assert detail["unit"]["name"] == "Oficina de Tecnologías de la Información"
    assert detail["parent"]["kind"] == "rectorado"
    titles = {p["title"] for p in detail["positions"]}
    assert "Oficial de Protección de Datos Personales" in titles
    dpo = next(p for p in detail["positions"] if p["title"].startswith("Oficial de Protección"))
    assert dpo["holder"]["full_name"]
    assert dpo["reports_to_title"] == "Jefe de la Oficina de Tecnologías de la Información"


@pytest.mark.ac("AC-002-12")
async def test_detalle_de_unidad_inexistente_404(client: httpx.AsyncClient, app) -> None:
    headers = await register_and_login(client)
    missing = "00000000-0000-0000-0000-000000000000"
    assert (await client.get(f"/org-units/{missing}", headers=headers)).status_code == 404
    assert (await client.get("/org-units/no-es-uuid", headers=headers)).status_code == 422


@pytest.mark.ac("AC-002-13")
async def test_systems_con_duenos_y_roles(client: httpx.AsyncClient, app) -> None:
    await load_university(app.state.session_factory)
    headers = await register_and_login(client)
    response = await client.get("/systems", headers=headers)
    assert response.status_code == 200
    systems = response.json()
    assert len(systems) == 8
    matricula = next(s for s in systems if s["name"] == "Sistema de Matrícula")
    assert matricula["owner_unit"]["code"] == "ORA"
    assert "datos académicos" in matricula["data_categories"]
    assert {o["role"] for o in matricula["owners"]} == {"controller", "processor", "steward"}
    assert (await client.get("/systems")).status_code == 401
