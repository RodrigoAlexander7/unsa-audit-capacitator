import httpx
import pytest

from tests.integration.conftest import register_and_login, superadmin_headers
from unsa_audit.seed.loader import sync_pims_requirements

pytestmark = pytest.mark.integration

CLAUSES = [
    "4.3",
    "5.2",
    "6.1.2",
    "6.1.3 e",
    "6.1.3 f",
    "6.1.3 c",
    "8.2",
    "8.3",
    "7.2",
    "9.1",
    "10.2",
]


@pytest.mark.ac("AC-005-1")
async def test_requisitos_en_orden_con_responsable(client: httpx.AsyncClient, seeded) -> None:
    headers = await register_and_login(client)
    response = await client.get("/pims/requirements", headers=headers)
    assert response.status_code == 200
    items = response.json()
    assert [r["clause_ref"] for r in items] == CLAUSES
    assert [r["order"] for r in items] == list(range(1, 12))
    scope = items[0]
    assert scope["document_kind"] == "PIMS_SCOPE" and scope["code"] == "pims-alcance"
    assert scope["responsible_unit_name"] == "Oficina de Tecnologías de la Información"
    assert items[1]["responsible_unit_name"] == "Rectorado"
    assert all(r["summary"] and r["expected_evidence"] for r in items)
    assert (await client.get("/pims/requirements")).status_code == 401


@pytest.mark.ac("AC-005-3")
@pytest.mark.ac("AC-005-6")
async def test_matriz_de_completitud_del_estado_sembrado(client: httpx.AsyncClient, seeded) -> None:
    headers = await register_and_login(client)
    response = await client.get("/pims/completeness", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert (body["total"], body["in_force"], body["percent_in_force"]) == (11, 5, 45)
    assert body["counts"] == {"in_force": 5, "draft": 2, "expired": 2, "unowned": 1, "missing": 1}
    assert body["as_of"]

    by_clause = {i["clause_ref"]: i for i in body["items"]}
    assert [i["clause_ref"] for i in body["items"]] == CLAUSES
    assert {c: i["state"] for c, i in by_clause.items()} == {
        "4.3": "in_force", "5.2": "in_force", "6.1.2": "expired", "6.1.3 e": "draft",
        "6.1.3 f": "unowned", "6.1.3 c": "in_force", "8.2": "in_force", "8.3": "draft",
        "7.2": "in_force", "9.1": "missing", "10.2": "expired",
    }  # fmt: skip
    assert by_clause["9.1"]["document"] is None and by_clause["9.1"]["issues"] == ["missing"]
    unowned = by_clause["6.1.3 f"]
    assert unowned["issues"] == ["unowned"]
    assert unowned["document"]["owner_unit_code"] is None
    assert unowned["document"]["code"] == "pims-plan-tratamiento"
    draft = by_clause["6.1.3 e"]["document"]
    assert (draft["lifecycle"], draft["review_date"], draft["current_version"]) == (
        "draft",
        None,
        1,
    )
    assert by_clause["6.1.2"]["document"]["review_date"] == "2025-06-30"
    assert (await client.get("/pims/completeness")).status_code == 401


@pytest.mark.ac("AC-005-5")
async def test_documentos_exponen_ciclo_de_vida_y_revision(
    client: httpx.AsyncClient, seeded
) -> None:
    headers = await register_and_login(client)
    docs = {d["code"]: d for d in (await client.get("/documents", headers=headers)).json()}
    assert docs["rof"]["lifecycle"] == "in_force" and docs["rof"]["review_date"] is None
    assert docs["pims-soa"]["lifecycle"] == "draft"
    assert docs["pims-soa"]["kind"] == "PIMS_SOA"
    detail = (await client.get("/documents/pims-no-conformidades", headers=headers)).json()
    assert (detail["lifecycle"], detail["review_date"]) == ("in_force", "2025-09-30")
    assert "NC-03" in detail["content_md"]


@pytest.mark.ac("AC-005-8")
async def test_un_documento_pims_se_modifica_como_cualquier_otro(
    client: httpx.AsyncClient, seeded
) -> None:
    learner = await register_and_login(client)
    admin = await superadmin_headers(client, seeded)
    before = (await client.get("/pims/completeness", headers=learner)).json()

    current = (await client.get("/documents/pims-alcance", headers=learner)).json()["content_md"]
    proposal = await client.post(
        "/documents/pims-alcance/change-requests",
        json={
            "title": "Incluir las facultades en el alcance",
            "rationale": "Segunda etapa del PIMS",
            "impact": "estructural",
            "proposed_content_md": current + "\n- Se incorporan las facultades.\n",
        },
        headers=learner,
    )
    assert proposal.status_code == 201
    approved = await client.post(
        f"/change-requests/{proposal.json()['id']}/resolve",
        json={"decision": "approve", "note": ""},
        headers=admin,
    )
    assert approved.status_code == 200 and approved.json()["resulting_version"] == 2

    after = (await client.get("/pims/completeness", headers=learner)).json()
    assert after["counts"] == before["counts"], "una nueva version no cambia el estado"
    scope = next(i for i in after["items"] if i["clause_ref"] == "4.3")
    assert scope["document"]["current_version"] == 2


@pytest.mark.ac("AC-005-6")
async def test_sync_de_requisitos_es_idempotente(client: httpx.AsyncClient, seeded) -> None:
    sf, settings = seeded.state.session_factory, seeded.state.settings
    assert await sync_pims_requirements(sf, settings) == 11
    assert await sync_pims_requirements(sf, settings) == 11
    headers = await register_and_login(client)
    assert len((await client.get("/pims/requirements", headers=headers)).json()) == 11
