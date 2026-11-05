"""Cadena R1 -> R4: prerrequisitos, modulos planned y demos de las Rutas 2-4."""

from uuid import uuid4

import httpx
import pytest
from sqlalchemy import text

from tests.integration.conftest import register_and_login, solve_module
from unsa_audit.learning.infrastructure.models import ModuleModel

pytestmark = pytest.mark.integration

ROUTES = ["sensibilizacion", "interpretacion", "implementacion", "auditor"]


async def _detail(client, headers, code):
    response = await client.get(f"/routes/{code}", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


async def _enroll(client, headers, code):
    return await client.post(f"/routes/{code}/enroll", headers=headers)


async def _pass_all_published(client, app, headers, code):
    detail = await _detail(client, headers, code)
    result = None
    for module in detail["modules"]:
        if module["planned"]:
            continue
        answer = await solve_module(app, module["id"])
        response = await client.post(
            f"/modules/{module['id']}/attempts", json={"answer": answer}, headers=headers
        )
        assert response.status_code == 200, response.text
        result = response.json()
    assert result is not None, "la ruta no tiene modulos publicados"
    return result


@pytest.mark.ac("AC-006-2")
@pytest.mark.ac("AC-010-1")
@pytest.mark.ac("AC-011-1")
@pytest.mark.ac("AC-012-1")
async def test_la_estructura_de_las_rutas_2_a_4_y_sus_modulos_planned(
    client: httpx.AsyncClient, seeded
) -> None:
    headers = await register_and_login(client)
    listing = (await client.get("/routes", headers=headers)).json()["routes"]
    by_code = {r["code"]: r for r in listing}
    assert [(c, by_code[c]["modules_total"], by_code[c]["modules_planned"]) for c in ROUTES] == [
        ("sensibilizacion", 7, 0),
        ("interpretacion", 8, 0),
        ("implementacion", 9, 0),
        ("auditor", 10, 0),
    ]

    for code in ROUTES[1:]:
        detail = await _detail(client, headers, code)
        assert not [m for m in detail["modules"] if m["planned"]]
        assert len(detail["modules"]) == detail["route"]["modules_total"]


@pytest.mark.ac("AC-006-2")
async def test_un_modulo_planned_responde_409(client: httpx.AsyncClient, seeded) -> None:
    headers = await register_and_login(client)
    assert (await _enroll(client, headers, "sensibilizacion")).status_code == 201

    planned_id = uuid4()
    async with seeded.state.session_factory() as session:
        session.add(
            ModuleModel(
                id=planned_id,
                route_code="sensibilizacion",
                slug="modulo-planned-sintetico",
                order=98,
                title="Módulo futuro sintético",
                minutes=10,
                mandatory=False,
                is_final=False,
                planned=True,
                lesson_md="# Módulo futuro",
                pass_score=70,
            )
        )
        await session.commit()

    assert (await client.get(f"/modules/{planned_id}", headers=headers)).status_code == 409
    attempt = await client.post(
        f"/modules/{planned_id}/attempts", json={"answer": {}}, headers=headers
    )
    assert attempt.status_code == 409
    assert (
        await client.post(f"/modules/{planned_id}/complete", headers=headers)
    ).status_code == 409


@pytest.mark.ac("AC-006-3")
@pytest.mark.ac("AC-006-8")
@pytest.mark.ac("AC-010-7")
@pytest.mark.ac("AC-011-7")
@pytest.mark.ac("AC-012-7")
async def test_cadena_completa_de_las_cuatro_rutas_acredita_horas_vigentes(
    client: httpx.AsyncClient, seeded
) -> None:
    headers = await register_and_login(client)

    # sin aprobar la anterior no se puede avanzar
    for code in ROUTES[1:]:
        blocked = await _enroll(client, headers, code)
        assert blocked.status_code == 409
        assert blocked.json()["detail"]["code"] == "prerequisite_not_met"

    for index, code in enumerate(ROUTES):
        assert (await _enroll(client, headers, code)).status_code == 201, code
        result = await _pass_all_published(client, seeded, headers, code)
        assert result["passed"] and result["route_completed"], code
        # la ruta siguiente sigue bloqueada hasta aprobar esta, y luego se habilita
        if index + 1 < len(ROUTES):
            routes = {
                r["code"]: r
                for r in (await client.get("/routes", headers=headers)).json()["routes"]
            }
            assert routes[code]["status"] == "completed"
            assert routes[ROUTES[index + 1]]["status"] == "available"
            for later in ROUTES[index + 2 :]:
                assert routes[later]["status"] == "locked"

    body = (await client.get("/routes", headers=headers)).json()
    hours = {r["code"]: r["hours_credited"] for r in body["routes"]}
    assert hours == {
        "sensibilizacion": 12.0,
        "interpretacion": 16.0,
        "implementacion": 24.0,
        "auditor": 32.0,
    }
    assert body["total_hours_credited"] == 84.0
    assert all(r["status"] == "completed" for r in body["routes"])


@pytest.mark.ac("AC-006-6")
@pytest.mark.ac("AC-011-2")
async def test_el_demo_de_implementacion_da_credito_parcial_y_aun_aprueba(
    client: httpx.AsyncClient, seeded
) -> None:
    headers = await register_and_login(client)
    for code in ROUTES[:2]:
        await _enroll(client, headers, code)
        await _pass_all_published(client, seeded, headers, code)
    await _enroll(client, headers, "implementacion")
    module = next(
        m for m in (await _detail(client, headers, "implementacion"))["modules"] if m["order"] == 4
    )

    spec = (await client.get(f"/modules/{module['id']}", headers=headers)).json()["exercise"]
    assert spec["kind"] == "soa_form"
    assert "applies" not in str(spec) and "explanation" not in str(spec)

    perfect = await solve_module(seeded, module["id"])
    half = {"decisions": {k: dict(v) for k, v in perfect["decisions"].items()}}
    for key in list(half["decisions"])[:4]:
        half["decisions"][key]["reason"] = "no-existe"
    response = await client.post(
        f"/modules/{module['id']}/attempts", json={"answer": half}, headers=headers
    )
    body = response.json()
    assert (body["score"], body["passed"], body["route_completed"]) == (75, True, False)
    assert sum(i["correct"] for i in body["items"]) == 4

    bad_shape = await client.post(
        f"/modules/{module['id']}/attempts", json={"answer": {"decisions": 5}}, headers=headers
    )
    assert bad_shape.status_code == 422


@pytest.mark.ac("AC-006-7")
@pytest.mark.ac("AC-012-2")
async def test_el_demo_de_auditoria_refleja_el_estado_real_del_pims(
    client: httpx.AsyncClient, seeded
) -> None:
    headers = await register_and_login(client)
    for code in ROUTES[:3]:
        await _enroll(client, headers, code)
        await _pass_all_published(client, seeded, headers, code)
    await _enroll(client, headers, "auditor")
    module = next(
        m for m in (await _detail(client, headers, "auditor"))["modules"] if m["order"] == 6
    )

    spec = (await client.get(f"/modules/{module['id']}", headers=headers)).json()["exercise"][
        "spec"
    ]
    texts = {i["id"]: i["label"] for i in spec["left"]}
    assert "No existe ningún documento" in texts["pims-monitoreo"]
    assert {r["label"] for r in spec["right"]} == {"Conforme", "Observación", "No conformidad"}

    # Publico el borrador de la SoA: pasa a vigente, asi que el hallazgo esperado cambia.
    before = await solve_module(seeded, module["id"])
    assert before["assignments"]["pims-soa"] == "no_conformidad"
    async with seeded.state.engine.begin() as conn:
        await conn.execute(
            text("UPDATE documents SET lifecycle = 'in_force' WHERE code = 'pims-soa'")
        )
    after = await solve_module(seeded, module["id"])
    assert after["assignments"]["pims-soa"] == "conforme"

    # la respuesta vieja ya no es perfecta, la nueva si
    old = await client.post(
        f"/modules/{module['id']}/attempts", json={"answer": before}, headers=headers
    )
    assert old.json()["score"] == 91  # 10 de 11
    new = await client.post(
        f"/modules/{module['id']}/attempts", json={"answer": after}, headers=headers
    )
    assert new.json()["score"] == 100 and new.json()["passed"] and not new.json()["route_completed"]
