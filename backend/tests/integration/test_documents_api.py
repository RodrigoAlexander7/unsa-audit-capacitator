import asyncio
import hashlib

import httpx
import pytest
from sqlalchemy import text

from tests.integration.conftest import register_and_login, superadmin_headers
from unsa_audit.seed.loader import sync_documents

pytestmark = pytest.mark.integration

CODES = ["cuadro-asignacion", "estatuto", "mof", "reglamento-evaluacion", "rof"]


async def _get(client, headers, path, **params):
    return await client.get(path, headers=headers, params=params)


async def _text(client, headers, code="rof") -> str:
    return (await _get(client, headers, f"/documents/{code}")).json()["content_md"]


async def _propose(client, headers, code="rof", suffix="\n## Nota\n\nTexto nuevo.\n", **overrides):
    body = {
        "title": "Añade una nota",
        "rationale": "Aclarar el alcance",
        "impact": "procedimental",
        "proposed_content_md": (await _text(client, headers, code)) + suffix,
    } | overrides
    return await client.post(f"/documents/{code}/change-requests", json=body, headers=headers)


async def _resolve(client, headers, change_id, decision="approve", note=""):
    return await client.post(
        f"/change-requests/{change_id}/resolve",
        json={"decision": decision, "note": note},
        headers=headers,
    )


# ---------------------------------------------------------------------------- lectura


@pytest.mark.ac("AC-004-1")
async def test_lista_de_documentos(client: httpx.AsyncClient, seeded) -> None:
    headers = await register_and_login(client)
    response = await _get(client, headers, "/documents")
    assert response.status_code == 200
    docs = {d["code"]: d for d in response.json()}
    assert sorted(c for c in docs if not c.startswith("pims-")) == CODES
    assert sum(c.startswith("pims-") for c in docs) == 10
    rof = docs["rof"]
    assert (rof["kind"], rof["current_version"], rof["open_change_requests"]) == ("ROF", 3, 0)
    assert rof["owner_unit_code"] == "SGEN" and rof["owner_unit_name"] == "Secretaría General"
    assert rof["updated_at"].startswith("2025-09-15")
    assert (await client.get("/documents")).status_code == 401


@pytest.mark.ac("AC-004-2")
async def test_detalle_del_documento_vigente(client: httpx.AsyncClient, seeded) -> None:
    headers = await register_and_login(client)
    response = await _get(client, headers, "/documents/rof")
    assert response.status_code == 200
    body = response.json()
    assert body["content_md"].startswith("# Reglamento de Organización y Funciones")
    assert "Artículo 6-A" in body["content_md"] and body["current_version"] == 3
    assert body["message"].startswith("Se asigna al Oficial")
    assert (await _get(client, headers, "/documents/nada")).status_code == 404


@pytest.mark.ac("AC-004-3")
async def test_versiones_y_contenido_por_numero(client: httpx.AsyncClient, seeded) -> None:
    headers = await register_and_login(client)
    versions = (await _get(client, headers, "/documents/rof/versions")).json()
    assert [v["number"] for v in versions] == [1, 2, 3]
    assert [v["parent_number"] for v in versions] == [None, 1, 2]
    assert versions[1]["message"] == "Corrección de errata en el artículo 5"
    assert versions[0]["author_label"] == "Secretaría General"

    v1 = (await _get(client, headers, "/documents/rof/versions/1")).json()
    assert "prescide" in v1["content_md"] and v1["document_code"] == "rof"
    assert (await _get(client, headers, "/documents/rof/versions/9")).status_code == 404
    assert (await _get(client, headers, "/documents/nada/versions")).status_code == 404


@pytest.mark.ac("AC-004-4")
async def test_diff_entre_versiones(client: httpx.AsyncClient, seeded) -> None:
    headers = await register_and_login(client)
    explicit = (await _get(client, headers, "/documents/rof/diff", **{"from": 1, "to": 2})).json()
    default = (await _get(client, headers, "/documents/rof/diff", to=2)).json()
    assert explicit == default
    assert (explicit["from_version"], explicit["to_version"]) == (1, 2)
    assert (explicit["additions"], explicit["deletions"]) == (1, 1)
    kinds = {line["kind"] for hunk in explicit["hunks"] for line in hunk["lines"]}
    assert kinds == {"add", "del", "ctx"}

    same = (await _get(client, headers, "/documents/rof/diff", **{"from": 3, "to": 3})).json()
    assert same["hunks"] == [] and same["additions"] == 0
    assert (await _get(client, headers, "/documents/rof/diff", to=9)).status_code == 404
    assert (await _get(client, headers, "/documents/rof/diff", to=1)).status_code == 404
    assert (await _get(client, headers, "/documents/nada/diff", to=2)).status_code == 404
    assert (await _get(client, headers, "/documents/rof/diff")).status_code == 422


# ---------------------------------------------------------------------------- propuestas


@pytest.mark.ac("AC-004-5")
async def test_cualquier_usuario_puede_proponer_un_cambio(
    client: httpx.AsyncClient, seeded
) -> None:
    headers = await register_and_login(client)
    response = await _propose(client, headers)
    assert response.status_code == 201, response.text
    body = response.json()
    assert (
        body["status"] == "open" and body["base_version"] == 3 and body["impact"] == "procedimental"
    )
    assert body["proposed_by_name"] == "Ana Quispe" and body["resolved_by_name"] is None
    docs = {d["code"]: d for d in (await _get(client, headers, "/documents")).json()}
    assert docs["rof"]["open_change_requests"] == 1
    no_auth = await client.post("/documents/rof/change-requests", json={})
    assert no_auth.status_code == 401


@pytest.mark.ac("AC-004-6")
@pytest.mark.parametrize(
    "overrides",
    [
        {"title": "   "},
        {"rationale": ""},
        {"impact": "enorme"},
        {"title": "t" * 201},
        {"proposed_content_md": "x" * 200_001},
        {"proposed_content_md": "   \n  "},
    ],
)
async def test_propuesta_invalida_da_422(client: httpx.AsyncClient, seeded, overrides) -> None:
    headers = await register_and_login(client)
    assert (await _propose(client, headers, **overrides)).status_code == 422


@pytest.mark.ac("AC-004-6")
async def test_propuesta_sin_cambios_reales_da_422(client: httpx.AsyncClient, seeded) -> None:
    headers = await register_and_login(client)
    current = await _text(client, headers)
    for same in (current, current.replace("\n", "\r\n"), current + "\n\n   \n"):
        response = await _propose(client, headers, proposed_content_md=same)
        assert response.status_code == 422, "solo formato"
        assert "no cambia" in response.json()["detail"]
    unknown = await client.post(
        "/documents/nada/change-requests",
        json={"title": "t", "rationale": "r", "impact": "cosmetico", "proposed_content_md": "x"},
        headers=headers,
    )
    assert unknown.status_code == 404


@pytest.mark.ac("AC-004-7")
async def test_listado_filtrado_y_detalle_con_diff(client: httpx.AsyncClient, seeded) -> None:
    headers = await register_and_login(client)
    admin = await superadmin_headers(client, seeded)
    first = (await _propose(client, headers)).json()
    second = (await _propose(client, headers, code="mof", suffix="\nNota.\n")).json()
    await _resolve(client, admin, second["id"], "reject", "No procede")

    everything = (await _get(client, headers, "/change-requests")).json()
    assert {c["id"] for c in everything} == {first["id"], second["id"]}
    opened = (await _get(client, headers, "/change-requests", status="open")).json()
    assert [c["id"] for c in opened] == [first["id"]]
    rejected = (
        await _get(client, headers, "/documents/mof/change-requests", status="rejected")
    ).json()
    assert [c["id"] for c in rejected] == [second["id"]]
    assert (await _get(client, headers, "/change-requests", status="otro")).status_code == 422
    assert (await _get(client, headers, "/documents/nada/change-requests")).status_code == 404

    detail = (await _get(client, headers, f"/change-requests/{first['id']}")).json()
    assert detail["diff"]["additions"] >= 3 and detail["diff"]["deletions"] == 0
    assert "Texto nuevo." in detail["proposed_content_md"]
    missing = "00000000-0000-0000-0000-000000000000"
    assert (await _get(client, headers, f"/change-requests/{missing}")).status_code == 404


# ---------------------------------------------------------------------------- resolucion


@pytest.mark.ac("AC-004-8")
async def test_solo_el_superadmin_resuelve(client: httpx.AsyncClient, seeded) -> None:
    learner = await register_and_login(client)
    change = (await _propose(client, learner)).json()
    assert (await _resolve(client, learner, change["id"])).status_code == 403
    assert (
        await client.post(f"/change-requests/{change['id']}/resolve", json={"decision": "approve"})
    ).status_code == 401
    still = (await _get(client, learner, f"/change-requests/{change['id']}")).json()
    assert still["status"] == "open"


@pytest.mark.ac("AC-004-9")
async def test_aprobar_crea_version_nueva_con_trazabilidad(
    client: httpx.AsyncClient, seeded
) -> None:
    learner = await register_and_login(client)
    admin = await superadmin_headers(client, seeded)
    change = (await _propose(client, learner)).json()

    response = await _resolve(client, admin, change["id"], "approve", "De acuerdo")
    assert response.status_code == 200, response.text
    resolved = response.json()
    assert resolved["status"] == "approved" and resolved["resulting_version"] == 4
    assert resolved["resolved_by_name"] == "Superadministrador"
    assert resolved["resolution_note"] == "De acuerdo" and resolved["resolved_at"]

    doc = (await _get(client, learner, "/documents/rof")).json()
    assert doc["current_version"] == 4 and doc["open_change_requests"] == 0
    assert doc["author_label"] == "Ana Quispe" and doc["message"] == "Añade una nota"
    assert "Texto nuevo." in doc["content_md"]

    versions = (await _get(client, learner, "/documents/rof/versions")).json()
    assert [v["number"] for v in versions] == [1, 2, 3, 4] and versions[-1]["parent_number"] == 3
    version_diff = (await _get(client, learner, "/documents/rof/diff", to=4)).json()
    request_diff = (await _get(client, learner, f"/change-requests/{change['id']}")).json()["diff"]
    assert version_diff["hunks"] == request_diff["hunks"]
    assert (version_diff["additions"], version_diff["deletions"]) == (
        request_diff["additions"],
        request_diff["deletions"],
    )


@pytest.mark.ac("AC-004-10")
async def test_base_obsoleta_da_409_y_la_solicitud_sigue_abierta(
    client: httpx.AsyncClient, seeded
) -> None:
    learner = await register_and_login(client)
    admin = await superadmin_headers(client, seeded)
    first = (await _propose(client, learner, suffix="\nA\n")).json()
    second = (await _propose(client, learner, suffix="\nB\n")).json()

    assert (await _resolve(client, admin, first["id"])).status_code == 200
    stale = await _resolve(client, admin, second["id"])
    assert stale.status_code == 409 and stale.json()["detail"]["code"] == "stale_base"
    detail = (await _get(client, learner, f"/change-requests/{second['id']}")).json()
    assert detail["status"] == "open"
    assert (await _resolve(client, admin, second["id"], "reject", "obsoleta")).status_code == 200


@pytest.mark.ac("AC-004-11")
async def test_rechazar_y_errores_de_resolucion(client: httpx.AsyncClient, seeded) -> None:
    learner = await register_and_login(client)
    admin = await superadmin_headers(client, seeded)
    change = (await _propose(client, learner)).json()

    assert (await _resolve(client, admin, change["id"], "quizas")).status_code == 422
    rejected = await _resolve(client, admin, change["id"], "reject", "No procede")
    assert rejected.status_code == 200
    body = rejected.json()
    assert body["status"] == "rejected" and body["resulting_version"] is None
    assert (await _get(client, learner, "/documents/rof")).json()["current_version"] == 3

    again = await _resolve(client, admin, change["id"], "approve")
    assert again.status_code == 409 and again.json()["detail"]["code"] == "already_resolved"
    missing = "00000000-0000-0000-0000-000000000000"
    assert (await _resolve(client, admin, missing)).status_code == 404


@pytest.mark.ac("AC-004-9")
@pytest.mark.ac("AC-004-10")
async def test_aprobaciones_simultaneas_de_la_misma_solicitud_solo_una_gana(
    client: httpx.AsyncClient, seeded
) -> None:
    learner = await register_and_login(client)
    admin = await superadmin_headers(client, seeded)
    change = (await _propose(client, learner)).json()

    results = await asyncio.gather(
        *(_resolve(client, admin, change["id"], "approve") for _ in range(4))
    )
    codes = sorted(r.status_code for r in results)
    assert codes.count(200) == 1 and all(c == 409 for c in codes if c != 200)
    versions = (await _get(client, learner, "/documents/rof/versions")).json()
    assert [v["number"] for v in versions] == [1, 2, 3, 4], "una sola version nueva"


@pytest.mark.ac("AC-004-12")
async def test_hash_y_cadena_de_todas_las_versiones(client: httpx.AsyncClient, seeded) -> None:
    learner = await register_and_login(client)
    admin = await superadmin_headers(client, seeded)
    await _resolve(client, admin, (await _propose(client, learner)).json()["id"])

    for code in CODES:
        versions = (await _get(client, learner, f"/documents/{code}/versions")).json()
        assert [v["number"] for v in versions] == list(range(1, len(versions) + 1))
        for v in versions:
            content = (
                await _get(client, learner, f"/documents/{code}/versions/{v['number']}")
            ).json()
            assert v["content_hash"] == hashlib.sha256(content["content_md"].encode()).hexdigest()
            assert v["parent_number"] == (v["number"] - 1 if v["number"] > 1 else None)


# ---------------------------------------------------------------------------- seed


@pytest.mark.ac("AC-004-14")
async def test_seed_idempotente_no_pisa_lo_de_la_app_y_reset_restaura(
    client: httpx.AsyncClient, seeded
) -> None:
    sf, settings = seeded.state.session_factory, seeded.state.settings
    learner = await register_and_login(client)
    admin = await superadmin_headers(client, seeded)
    await _resolve(client, admin, (await _propose(client, learner)).json()["id"])

    assert await sync_documents(sf, settings) == (0, 15)
    async with seeded.state.engine.connect() as conn:
        counts = (
            await conn.scalar(text("SELECT count(*) FROM documents")),
            await conn.scalar(text("SELECT count(*) FROM document_versions")),
        )
    # 5 generales (9 versiones) + la v4 del ROF creada desde la app + 10 documentos PIMS
    assert counts == (15, 9 + 1 + 10)
    assert (await _get(client, learner, "/documents/rof")).json()["current_version"] == 4

    assert await sync_documents(sf, settings, reset=True) == (15, 0)
    assert (await _get(client, learner, "/documents/rof")).json()["current_version"] == 3
    assert (await _get(client, learner, "/change-requests")).json() == []
