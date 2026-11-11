import shutil
from pathlib import Path

import httpx
import pytest
from sqlalchemy import text

from tests.integration.conftest import register_and_login, solve_module
from unsa_audit.learning.application.use_cases import SyncContent
from unsa_audit.learning.infrastructure.content_loader import FileContentSource
from unsa_audit.learning.infrastructure.sqlalchemy_repository import SqlAlchemyLearningRepository

pytestmark = pytest.mark.integration

R1 = "sensibilizacion"
SOLUTION_KEYS = {"correct", "correct_order", "pairs", "points", "feedback", "explanation"}


def _keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {k for v in value.values() for k in _keys(v)}
    if isinstance(value, list):
        return {k for v in value for k in _keys(v)}
    return set()


async def _routes(client: httpx.AsyncClient, headers: dict) -> dict:
    response = await client.get("/routes", headers=headers)
    assert response.status_code == 200
    return {r["code"]: r for r in response.json()["routes"]} | {
        "_total": response.json()["total_hours_credited"]
    }


async def _modules(client: httpx.AsyncClient, headers: dict, code: str = R1) -> list[dict]:
    response = await client.get(f"/routes/{code}", headers=headers)
    assert response.status_code == 200
    return response.json()["modules"]


async def _enroll_r1(client: httpx.AsyncClient, headers: dict) -> None:
    assert (await client.post(f"/routes/{R1}/enroll", headers=headers)).status_code == 201


async def _pass(client, app, headers, module_id: str) -> dict:
    answer = await solve_module(app, module_id)
    response = await client.post(
        f"/modules/{module_id}/attempts", json={"answer": answer}, headers=headers
    )
    assert response.status_code == 200, response.text
    return response.json()


# ---------------------------------------------------------------------------- catalogo


@pytest.mark.ac("AC-003-1")
async def test_catalogo_inicial_de_un_usuario_nuevo(client: httpx.AsyncClient, seeded) -> None:
    headers = await register_and_login(client)
    routes = await _routes(client, headers)
    assert [(c, routes[c]["hours"], routes[c]["status"]) for c in
            ("sensibilizacion", "interpretacion", "implementacion", "auditor")] == [
        ("sensibilizacion", 12, "available"),
        ("interpretacion", 16, "locked"),
        ("implementacion", 24, "locked"),
        ("auditor", 32, "locked"),
    ]  # fmt: skip
    assert routes["interpretacion"]["prerequisite_code"] == "sensibilizacion"
    assert routes[R1]["modules_total"] == 7 and routes["_total"] == 0
    assert (await client.get("/routes")).status_code == 401


@pytest.mark.ac("AC-003-2")
async def test_matricula_201_y_luego_200_idempotente(client: httpx.AsyncClient, seeded) -> None:
    headers = await register_and_login(client)
    first = await client.post(f"/routes/{R1}/enroll", headers=headers)
    again = await client.post(f"/routes/{R1}/enroll", headers=headers)
    assert (first.status_code, again.status_code) == (201, 200)
    assert first.json()["status"] == "in_progress"
    assert first.json() == again.json()
    assert (await _routes(client, headers))[R1]["status"] == "in_progress"


@pytest.mark.ac("AC-003-3")
async def test_gating_de_prerrequisitos(client: httpx.AsyncClient, seeded) -> None:
    headers = await register_and_login(client)
    for code in ("interpretacion", "auditor"):
        response = await client.post(f"/routes/{code}/enroll", headers=headers)
        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "prerequisite_not_met"
    await _enroll_r1(client, headers)  # matriculado pero no aprobado
    assert (await client.post("/routes/interpretacion/enroll", headers=headers)).status_code == 409


@pytest.mark.ac("AC-003-4")
async def test_ruta_inexistente_404(client: httpx.AsyncClient, seeded) -> None:
    headers = await register_and_login(client)
    assert (await client.post("/routes/nada/enroll", headers=headers)).status_code == 404
    assert (await client.get("/routes/nada", headers=headers)).status_code == 404


@pytest.mark.ac("AC-003-5")
async def test_modulos_de_la_ruta_y_su_estado(client: httpx.AsyncClient, seeded) -> None:
    headers = await register_and_login(client)
    before = await _modules(client, headers)
    assert [m["order"] for m in before] == list(range(1, 8))
    assert {m["status"] for m in before} == {"locked"}
    await _enroll_r1(client, headers)
    after = await _modules(client, headers)
    assert [m["status"] for m in after] == ["available"] * 6 + ["locked"]
    assert after[-1]["is_final"] and after[0]["minutes"] == 100 and after[0]["has_exercise"]


# ---------------------------------------------------------------------------- modulos


@pytest.mark.ac("AC-003-6")
async def test_modulo_exige_matricula_y_no_filtra_soluciones(
    client: httpx.AsyncClient, seeded
) -> None:
    headers = await register_and_login(client)
    modules = await _modules(client, headers)
    first_id, final_id = modules[0]["id"], modules[-1]["id"]

    assert (await client.get(f"/modules/{first_id}", headers=headers)).status_code == 403
    await _enroll_r1(client, headers)

    for module in modules[:-1]:
        response = await client.get(f"/modules/{module['id']}", headers=headers)
        assert response.status_code == 200, module["title"]
        body = response.json()
        assert body["lesson_md"].startswith("#")
        assert body["exercise"]["kind"] in {"ordering", "matching", "quiz", "branching"}
        leaked = _keys(body["exercise"]["spec"]) & SOLUTION_KEYS
        assert not leaked, f"{module['title']}: {leaked}"

    assert (await client.get(f"/modules/{final_id}", headers=headers)).status_code == 409
    missing = "00000000-0000-0000-0000-000000000000"
    assert (await client.get(f"/modules/{missing}", headers=headers)).status_code == 404
    assert (await client.get(f"/modules/{first_id}")).status_code == 401


@pytest.mark.ac("AC-003-8")
async def test_intento_incorrecto_correcto_e_invalido(client: httpx.AsyncClient, seeded) -> None:
    headers = await register_and_login(client)
    await _enroll_r1(client, headers)
    module = (await _modules(client, headers))[2]  # normas internas: ordering
    url = f"/modules/{module['id']}/attempts"

    bad = await client.post(url, json={"answer": {"order": []}}, headers=headers)
    assert bad.status_code == 200
    assert (bad.json()["score"], bad.json()["passed"], bad.json()["module_completed"]) == (
        0,
        False,
        False,
    )

    for payload in ({"answer": {"order": "x"}}, {"answer": "x"}, {}):
        assert (await client.post(url, json=payload, headers=headers)).status_code == 422

    good = await _pass(client, seeded, headers, module["id"])
    assert (good["score"], good["passed"], good["module_completed"]) == (100, True, True)
    assert len(good["items"]) == 6
    refreshed = (await _modules(client, headers))[2]
    assert refreshed["status"] == "completed" and refreshed["best_score"] == 100


@pytest.mark.ac("AC-003-9")
async def test_los_ejercicios_generados_reflejan_la_bd(client: httpx.AsyncClient, seeded) -> None:
    headers = await register_and_login(client)
    await _enroll_r1(client, headers)
    modules = await _modules(client, headers)
    owners_module = modules[3]  # datos y sistemas: system_owners

    async with seeded.state.engine.begin() as conn:
        await conn.execute(
            text(
                "UPDATE org_units SET name = 'Oficina de Registros (renombrada)' WHERE code = 'ORA'"
            )
        )
    spec = (await client.get(f"/modules/{owners_module['id']}", headers=headers)).json()[
        "exercise"
    ]["spec"]
    assert "Oficina de Registros (renombrada)" in {r["label"] for r in spec["right"]}
    result = await _pass(client, seeded, headers, owners_module["id"])
    assert result["score"] == 100


@pytest.mark.ac("AC-003-13")
async def test_completar_un_modulo_con_ejercicio_da_409(client: httpx.AsyncClient, seeded) -> None:
    headers = await register_and_login(client)
    await _enroll_r1(client, headers)
    first = (await _modules(client, headers))[0]
    response = await client.post(f"/modules/{first['id']}/complete", headers=headers)
    assert response.status_code == 409


@pytest.mark.ac("AC-003-14")
async def test_los_intentos_quedan_registrados(client: httpx.AsyncClient, seeded) -> None:
    headers = await register_and_login(client)
    await _enroll_r1(client, headers)
    module = (await _modules(client, headers))[2]
    await client.post(
        f"/modules/{module['id']}/attempts", json={"answer": {"order": []}}, headers=headers
    )
    await _pass(client, seeded, headers, module["id"])
    async with seeded.state.engine.connect() as conn:
        rows = (
            await conn.execute(
                text("SELECT score, passed FROM exercise_attempts ORDER BY created_at")
            )
        ).all()
    assert [tuple(r) for r in rows] == [(0, False), (100, True)]


# ---------------------------------------------------------------------------- ruta completa


@pytest.mark.ac("AC-003-10")
@pytest.mark.ac("AC-003-11")
@pytest.mark.ac("AC-003-12")
async def test_completar_la_ruta_1_acredita_12_horas_y_desbloquea_la_ruta_2(
    client: httpx.AsyncClient, seeded
) -> None:
    headers = await register_and_login(client)
    await _enroll_r1(client, headers)
    modules = await _modules(client, headers)

    for module in modules[:-1]:
        result = await _pass(client, seeded, headers, module["id"])
        assert result["module_completed"] and not result["route_completed"]

    mid = await _routes(client, headers)
    assert mid[R1]["status"] == "in_progress" and mid[R1]["hours_credited"] == 10.5  # 630 min
    assert mid["interpretacion"]["status"] == "locked"
    assert (await client.post("/routes/interpretacion/enroll", headers=headers)).status_code == 409

    final = await _pass(client, seeded, headers, modules[-1]["id"])
    assert final["route_completed"] and final["passed"]

    done = await _routes(client, headers)
    assert done[R1]["status"] == "completed"
    assert (done[R1]["hours_credited"], done["_total"]) == (12.0, 12.0)
    assert done["interpretacion"]["status"] == "available"
    assert (await client.post("/routes/interpretacion/enroll", headers=headers)).status_code == 201

    # reintentar un modulo ya completado: no suma horas y conserva el mejor puntaje
    await client.post(
        f"/modules/{modules[0]['id']}/attempts",
        json={"answer": {"assignments": {}}},
        headers=headers,
    )
    after = await _routes(client, headers)
    assert after["_total"] == 12.0
    assert (await _modules(client, headers))[0]["best_score"] == 100


@pytest.mark.ac("AC-003-10")
async def test_el_final_esta_bloqueado_hasta_completar_los_demas(
    client: httpx.AsyncClient, seeded
) -> None:
    headers = await register_and_login(client)
    await _enroll_r1(client, headers)
    modules = await _modules(client, headers)
    final = modules[-1]
    response = await client.post(
        f"/modules/{final['id']}/attempts", json={"answer": {"answers": {}}}, headers=headers
    )
    assert response.status_code == 409
    for module in modules[:-2]:
        await _pass(client, seeded, headers, module["id"])
    assert (await client.get(f"/modules/{final['id']}", headers=headers)).status_code == 409
    await _pass(client, seeded, headers, modules[-2]["id"])
    assert (await client.get(f"/modules/{final['id']}", headers=headers)).status_code == 200


@pytest.mark.ac("AC-003-10")
async def test_suspender_la_evaluacion_final_no_completa_la_ruta(
    client: httpx.AsyncClient, seeded
) -> None:
    headers = await register_and_login(client)
    await _enroll_r1(client, headers)
    modules = await _modules(client, headers)
    for module in modules[:-1]:
        await _pass(client, seeded, headers, module["id"])
    failed = await client.post(
        f"/modules/{modules[-1]['id']}/attempts", json={"answer": {"answers": {}}}, headers=headers
    )
    assert failed.json()["passed"] is False and failed.json()["route_completed"] is False
    assert (await _routes(client, headers))[R1]["status"] == "in_progress"


# ---------------------------------------------------------------------------- contenido


@pytest.mark.ac("AC-003-16")
async def test_el_sync_es_idempotente_y_elimina_modulos_retirados(seeded, tmp_path: Path) -> None:
    sf = seeded.state.session_factory
    repo = SqlAlchemyLearningRepository(sf)
    content = Path(seeded.state.settings.content_dir)

    before = await repo.list_modules()
    await SyncContent(repo, FileContentSource(content)).execute()
    again = await repo.list_modules()
    assert [m.id for m in before] == [m.id for m in again] and len(before) == 34  # 7+8+9+10

    trimmed = tmp_path / "content"
    shutil.copytree(content, trimmed)
    for leftover in (trimmed / "routes" / "1-sensibilizacion").glob("06-*"):
        leftover.unlink()
    await SyncContent(repo, FileContentSource(trimmed)).execute()
    assert len(await repo.list_modules()) == 33
