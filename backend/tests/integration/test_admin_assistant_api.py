"""Pruebas de integracion HTTP/DB del asistente administrador y reestructuracion (F13)."""

import json
from uuid import uuid4

import httpx
import pytest

from tests.integration.conftest import register_and_login, superadmin_headers
from unsa_audit.assistant.application.ports import ModelAnswer

pytestmark = pytest.mark.integration


class FakeAdminAssistantModel:
    def __init__(self) -> None:
        self.prompts: list[str] = []
        self.reply = "En el cohorte evaluado, **P-01** ya avanzó en sensibilización y **P-02** requiere seguimiento."

    async def ask(self, prompt: str) -> ModelAnswer:
        self.prompts.append(prompt)
        return ModelAnswer(text=self.reply, duration_ms=13)


@pytest.fixture
def assistant_model() -> FakeAdminAssistantModel:
    return FakeAdminAssistantModel()


@pytest.mark.ac("AC-014-1")
async def test_endpoints_admin_exigen_superadmin(client: httpx.AsyncClient, seeded) -> None:
    assert (await client.get("/assistant/admin/cohort")).status_code == 401
    assert (await client.post("/assistant/admin/ask", json={"question": "hola"})).status_code == 401
    assert (await client.post("/assistant/admin/proposals/generate", json={})).status_code == 401

    learner = await register_and_login(client, "ana@example.com")
    assert (await client.get("/assistant/admin/cohort", headers=learner)).status_code == 403
    assert (
        await client.post("/assistant/admin/ask", json={"question": "hola"}, headers=learner)
    ).status_code == 403
    assert (
        await client.post("/assistant/admin/proposals/generate", json={}, headers=learner)
    ).status_code == 403
    assert (await client.get("/assistant/admin/proposals", headers=learner)).status_code == 403
    assert (
        await client.patch(
            f"/assistant/admin/proposals/{uuid4()}",
            json={"status": "accepted"},
            headers=learner,
        )
    ).status_code == 403


@pytest.mark.ac("AC-014-2")
@pytest.mark.ac("AC-014-3")
async def test_consulta_admin_seudonimiza_hacia_ia_y_devuelve_tabla_alias(
    client: httpx.AsyncClient, seeded, assistant_model: FakeAdminAssistantModel
) -> None:
    await register_and_login(client, "ana@example.com")
    await client.post(
        "/auth/register",
        json={
            "email": "carlos.soto@example.com",
            "password": "password123",
            "full_name": "Carlos Soto Vargas",
        },
    )
    admin = await superadmin_headers(client, seeded)

    cohort = await client.get("/assistant/admin/cohort", headers=admin)
    assert cohort.status_code == 200, cohort.text
    cohort_data = cohort.json()
    assert cohort_data["total_learners"] == 2
    assert [a["alias"] for a in cohort_data["aliases"]] == ["P-01", "P-02"]
    assert cohort_data["aliases"][0]["email"] == "ana@example.com"
    assert cohort_data["aliases"][1]["email"] == "carlos.soto@example.com"

    # Incluso si el coordinador cita nombres y correos reales, `agy` recibe solo alias P-xx
    resp = await client.post(
        "/assistant/admin/ask",
        json={"question": "¿Cómo avanzan Ana Quispe (ana@example.com) y Carlos Soto Vargas?"},
        headers=admin,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "P-01" in body["message"]["answer"]
    assert len(body["aliases"]) == 2

    prompt = assistant_model.prompts[0]
    assert "P-01" in prompt and "P-02" in prompt
    for pii in (
        "Ana Quispe",
        "Carlos Soto",
        "ana@example.com",
        "carlos.soto@example.com",
        "superadmin@test.example",
        "@",
    ):
        assert pii not in prompt, f"No debe filtrarse PII ({pii}) hacia agy"


@pytest.mark.ac("AC-014-4")
@pytest.mark.ac("AC-014-5")
async def test_generar_y_revisar_borradores_de_reestructuracion(
    client: httpx.AsyncClient, seeded, assistant_model: FakeAdminAssistantModel
) -> None:
    await register_and_login(client, "ana@example.com")
    admin = await superadmin_headers(client, seeded)

    # Respuesta invalida de IA -> 502 sin ensuciar BD
    assistant_model.reply = "texto sin json"
    bad = await client.post("/assistant/admin/proposals/generate", json={}, headers=admin)
    assert bad.status_code == 502
    assert (await client.get("/assistant/admin/proposals", headers=admin)).json() == []

    # Respuesta valida estructurada -> persiste borradores `draft`
    routes_before = (await client.get("/routes", headers=admin)).json()
    assistant_model.reply = json.dumps(
        {
            "summary": "Reforzar normas internas en Ruta 1.",
            "proposals": [
                {
                    "title": "Añadir guía de jerarquía normativa",
                    "target_route_code": "sensibilizacion",
                    "target_module_slug": "03-normas-internas",
                    "change_type": "add_practice",
                    "proposed_change": "Incorporar un cuadro comparativo previo al ejercicio.",
                    "rationale": "P-01 presentó dificultades en ordenamiento normativo.",
                    "evidence_metrics": {"affected_aliases": ["P-01"]},
                }
            ],
        }
    )
    gen = await client.post(
        "/assistant/admin/proposals/generate",
        json={"focus": "Priorizar Ruta 1", "route_code": "sensibilizacion"},
        headers=admin,
    )
    assert gen.status_code == 201, gen.text
    gen_body = gen.json()
    assert gen_body["summary"] == "Reforzar normas internas en Ruta 1."
    assert len(gen_body["proposals"]) == 1
    prop_id = gen_body["proposals"][0]["id"]
    assert gen_body["proposals"][0]["status"] == "draft"

    # El curriculo publicado NO se muta automaticamente
    routes_after = (await client.get("/routes", headers=admin)).json()
    assert routes_after == routes_before

    # Revision: draft -> accepted -> discarded
    acc = await client.patch(
        f"/assistant/admin/proposals/{prop_id}",
        json={"status": "accepted", "review_note": "Programado para el próximo ciclo"},
        headers=admin,
    )
    assert acc.status_code == 200
    assert acc.json()["status"] == "accepted"
    assert acc.json()["reviewed_at"] is not None

    disc = await client.patch(
        f"/assistant/admin/proposals/{prop_id}",
        json={"status": "discarded", "review_note": "Reemplazado por otra mejora"},
        headers=admin,
    )
    assert disc.status_code == 200 and disc.json()["status"] == "discarded"

    assert (
        await client.patch(
            f"/assistant/admin/proposals/{uuid4()}",
            json={"status": "accepted"},
            headers=admin,
        )
    ).status_code == 404


@pytest.mark.ac("AC-014-6")
async def test_historial_admin_separado_del_historial_estudiante(
    client: httpx.AsyncClient, seeded, assistant_model: FakeAdminAssistantModel
) -> None:
    admin = await superadmin_headers(client, seeded)
    await client.post(
        "/assistant/ask", json={"question": "Pregunta modo estudiante"}, headers=admin
    )
    await client.post(
        "/assistant/admin/ask", json={"question": "Pregunta modo coordinador"}, headers=admin
    )

    student_hist = (await client.get("/assistant/history", headers=admin)).json()
    admin_hist = (await client.get("/assistant/admin/history", headers=admin)).json()
    assert [m["question"] for m in student_hist] == ["Pregunta modo estudiante"]
    assert [m["question"] for m in admin_hist] == ["Pregunta modo coordinador"]

    await client.delete("/assistant/admin/history", headers=admin)
    assert (await client.get("/assistant/admin/history", headers=admin)).json() == []
    assert len((await client.get("/assistant/history", headers=admin)).json()) == 1
