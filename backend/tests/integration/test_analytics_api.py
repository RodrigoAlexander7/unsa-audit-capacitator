import httpx
import pytest

from tests.integration.conftest import register_and_login, solve_module, superadmin_headers
from tests.solutions import wrong
from unsa_audit.analytics.application.errors import AdvisorTimeout, AdvisorUnavailable
from unsa_audit.analytics.application.ports import AdvisorAnswer
from unsa_audit.learning.domain.route import ExerciseKind

pytestmark = pytest.mark.integration

R1 = "sensibilizacion"


class FakeAdvisor:
    def __init__(self) -> None:
        self.prompts: list[str] = []
        self.error: Exception | None = None

    async def ask(self, prompt: str) -> AdvisorAnswer:
        self.prompts.append(prompt)
        if self.error:
            raise self.error
        return AdvisorAnswer(
            "## Diagnóstico\nDatos revisados.\n## Ajustes propuestos\n1. Refuerza el módulo 3.", 7
        )


@pytest.fixture
def advisor() -> FakeAdvisor:  # sobrescribe el fixture de conftest
    return FakeAdvisor()


async def _modules(client, headers, code=R1):
    return (await client.get(f"/routes/{code}", headers=headers)).json()["modules"]


async def _pass(client, app, headers, module_id):
    answer = await solve_module(app, module_id)
    response = await client.post(
        f"/modules/{module_id}/attempts", json={"answer": answer}, headers=headers
    )
    assert response.status_code == 200, response.text
    return response.json()


async def _fail(client, headers, module_id, kind: ExerciseKind):
    response = await client.post(
        f"/modules/{module_id}/attempts", json={"answer": wrong(kind)}, headers=headers
    )
    assert response.status_code == 200
    return response.json()


async def _populate(client, app):
    """Ana completa R1 y R2; Beto avanza 3 modulos de R1 y falla el 4; Carla solo se matricula;
    Dario falla dos veces el modulo 3. El superadmin tambien se matricula (no debe contar)."""
    users = {}
    for name in ("ana", "beto", "carla", "dario"):
        users[name] = await register_and_login(client, f"{name}@example.com")
        await client.post(f"/routes/{R1}/enroll", headers=users[name])
    admin = await superadmin_headers(client, app)
    await client.post(f"/routes/{R1}/enroll", headers=admin)
    await _pass(client, app, admin, (await _modules(client, admin))[0]["id"])

    for module in (await _modules(client, users["ana"]))[:-1]:
        await _pass(client, app, users["ana"], module["id"])
    final = (await _modules(client, users["ana"]))[-1]
    await _pass(client, app, users["ana"], final["id"])
    await client.post("/routes/interpretacion/enroll", headers=users["ana"])
    for mod in await _modules(client, users["ana"], "interpretacion"):
        if not mod["planned"]:
            await _pass(client, app, users["ana"], mod["id"])

    r1 = await _modules(client, users["beto"])
    for module in r1[:3]:
        await _pass(client, app, users["beto"], module["id"])
    await _fail(client, users["beto"], r1[3]["id"], ExerciseKind.MATCHING)

    for _ in range(2):
        await _fail(client, users["dario"], r1[2]["id"], ExerciseKind.ORDERING)
    return users, admin


async def _assessment(client, app, headers, profile, only_first: int | None = None):
    attempt = (await client.post("/assessments", json={"profile": profile}, headers=headers)).json()
    from unsa_audit.assessment.domain.assessment import Profile

    truth = {
        q.id: q.correct for q in app.state.start_assessment._bank.get(Profile(profile)).questions
    }
    ids = list(truth)[:only_first] if only_first is not None else list(truth)
    response = await client.post(
        f"/assessments/{attempt['id']}/submit",
        json={"answers": {qid: truth[qid] for qid in ids}},
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()


# ---------------------------------------------------------------------------- permisos


ADMIN_ENDPOINTS = [
    ("GET", "/admin/stats/routes"),
    ("GET", f"/admin/stats/routes/{R1}"),
    ("GET", "/admin/stats/assessments"),
    ("GET", "/admin/advisor/snapshot"),
    ("GET", "/admin/advisor/history"),
    ("POST", "/admin/advisor/ask"),
]


@pytest.mark.ac("AC-007-1")
@pytest.mark.parametrize(("method", "path"), ADMIN_ENDPOINTS)
async def test_solo_el_superadmin_accede(client: httpx.AsyncClient, seeded, method, path) -> None:
    learner = await register_and_login(client)
    payload = {"question": "hola"} if method == "POST" else None
    anonymous = await client.request(method, path, json=payload)
    assert anonymous.status_code == 401
    forbidden = await client.request(method, path, json=payload, headers=learner)
    assert forbidden.status_code == 403


# ---------------------------------------------------------------------------- estadisticas


@pytest.mark.ac("AC-007-1")
async def test_estadisticas_por_ruta_con_datos_reales(client: httpx.AsyncClient, seeded) -> None:
    _, admin = await _populate(client, seeded)
    response = await client.get("/admin/stats/routes", headers=admin)
    assert response.status_code == 200
    routes = response.json()
    assert [r["code"] for r in routes] == [
        "sensibilizacion",
        "interpretacion",
        "implementacion",
        "auditor",
    ]
    r1, r2, r3, r4 = routes

    assert (r1["enrolled"], r1["in_progress"], r1["completed"]) == (
        4,
        3,
        1,
    ), "el superadmin no cuenta"
    assert r1["completion_rate"] == 25 and r1["modules_total"] == 7
    assert r1["avg_progress"] == 36  # (7 + 3 + 0 + 0) / (4 * 7)
    assert (r1["attempts"], r1["pass_rate"]) == (13, 77)  # 13 intentos (7+4+2), 10 aprobados
    assert r1["stalled"] == 1, "solo Carla no intento nada"
    assert r1["avg_hours_credited"] == round(
        (720 + 310) / 60 / 4, 1
    )  # Ana 720 min; Beto 100+110+100

    assert (r2["enrolled"], r2["completed"], r2["completion_rate"]) == (1, 1, 100)
    assert r2["avg_hours_credited"] == 16.0 and r2["pass_rate"] == 100
    assert (r3["enrolled"], r3["attempts"], r4["enrolled"]) == (0, 0, 0)
    assert r3["completion_rate"] == 0 and r3["avg_hours_credited"] == 0.0


@pytest.mark.ac("AC-007-2")
async def test_detalle_de_ruta_con_modulos_y_dificiles(client: httpx.AsyncClient, seeded) -> None:
    _, admin = await _populate(client, seeded)
    response = await client.get(f"/admin/stats/routes/{R1}", headers=admin)
    assert response.status_code == 200
    body = response.json()
    assert body["route"]["code"] == R1
    modules = body["modules"]
    assert [m["order"] for m in modules] == list(range(1, 8)), "solo modulos publicados, en orden"
    third = modules[2]
    assert (third["attempts"], third["learners_attempted"], third["learners_completed"]) == (
        4,
        3,
        2,
    )
    assert third["pass_rate"] == 50 and third["hardest"] is True
    assert modules[3]["attempts"] == 2 and modules[3]["hardest"] is False, "pocos intentos"
    assert modules[6]["attempts"] == 1 and modules[6]["avg_score"] == 100
    assert (await client.get("/admin/stats/routes/nada", headers=admin)).status_code == 404

    r2_stats = (await client.get("/admin/stats/routes/interpretacion", headers=admin)).json()
    assert len(r2_stats["modules"]) == 8
    planned = (await client.get("/admin/stats/routes/implementacion", headers=admin)).json()
    assert len(planned["modules"]) == 1, "los modulos planned no aparecen"


@pytest.mark.ac("AC-007-3")
async def test_estadisticas_de_evaluaciones_por_competencia_y_requisito(
    client: httpx.AsyncClient, seeded
) -> None:
    users, admin = await _populate(client, seeded)
    await _assessment(client, seeded, users["ana"], "controller")
    await _assessment(client, seeded, users["beto"], "controller", only_first=0)
    await _assessment(client, seeded, users["dario"], "processor", only_first=6)
    await _assessment(client, seeded, admin, "controller")  # el superadmin no cuenta
    await client.post(
        "/assessments", json={"profile": "processor"}, headers=users["carla"]
    )  # en curso

    response = await client.get("/admin/stats/assessments", headers=admin)
    assert response.status_code == 200
    by_profile = {p["profile"]: p for p in response.json()}
    controller, processor = by_profile["controller"], by_profile["processor"]
    assert (controller["finished"], controller["avg_score"], controller["pass_rate"]) == (2, 50, 50)
    assert (processor["finished"], processor["avg_score"], processor["pass_rate"]) == (1, 50, 0)

    comps = {g["key"]: g for g in controller["competencies"]}
    assert comps["brechas"]["average"] == 50 and comps["brechas"]["samples"] == 2
    assert controller["competencies"][0]["average"] <= controller["competencies"][-1]["average"]
    assert all(g["label"] and g["label"][0].isdigit() for g in controller["requirements"])


# ---------------------------------------------------------------------------- snapshot y asesor


@pytest.mark.ac("AC-007-4")
async def test_snapshot_agregado_y_sin_datos_personales(client: httpx.AsyncClient, seeded) -> None:
    users, admin = await _populate(client, seeded)
    await _assessment(client, seeded, users["ana"], "controller")

    first = (await client.get("/admin/advisor/snapshot", headers=admin)).json()
    second = (await client.get("/admin/advisor/snapshot", headers=admin)).json()
    assert first["hash"] == second["hash"], "mismo estado, mismo hash"

    data = first["data"]
    assert data["participants"]["total"] == 4
    assert [r["title"] for r in data["routes"]][0].startswith("Sensibilización")
    assert data["routes"][0]["enrolled"] == 4
    assert any(m["among_hardest"] for m in data["modules"])
    assert data["assessments"][0]["profile"] == "controller"
    assert data["pims_documents"]["by_state"]["missing"] == 1
    assert data["pims_documents"]["open_change_requests"] == 0

    text = str(first)
    for personal in (
        "ana@example.com",
        "beto@example.com",
        "Ana Quispe",
        "superadmin@test.example",
        "@",
    ):
        assert personal not in text, personal

    await client.post(
        f"/routes/{R1}/enroll", headers=await register_and_login(client, "nuevo@example.com")
    )
    assert (await client.get("/admin/advisor/snapshot", headers=admin)).json()["hash"] != first[
        "hash"
    ]


@pytest.mark.ac("AC-007-6")
@pytest.mark.ac("AC-007-8")
async def test_preguntar_al_asesor_responde_y_registra(
    client: httpx.AsyncClient, seeded, advisor: FakeAdvisor
) -> None:
    _, admin = await _populate(client, seeded)
    question = "¿Cómo están los alumnos de sensibilización?"
    response = await client.post("/admin/advisor/ask", json={"question": question}, headers=admin)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "ok" and body["answer"].startswith("## Diagnóstico")
    assert (
        body["question"] == question
        and body["duration_ms"] == 7
        and len(body["snapshot_hash"]) == 64
    )

    prompt = advisor.prompts[0]
    assert prompt.count(question) == 1 and "Reglas:" in prompt and "asesor pedagógico" in prompt
    assert '"enrolled": 4' in prompt, "los datos reales viajan en el prompt"
    for personal in ("ana@example.com", "Ana Quispe", "@"):
        assert personal not in prompt


@pytest.mark.ac("AC-007-6")
@pytest.mark.parametrize(
    ("error", "fragment"),
    [
        (AdvisorUnavailable("No se encontró el comando de la IA (agy)."), "No se encontró"),
        (AdvisorTimeout("La IA tardó demasiado en responder."), "tardó demasiado"),
    ],
)
async def test_si_el_asesor_falla_responde_502_y_queda_registrado(
    client: httpx.AsyncClient, seeded, advisor: FakeAdvisor, error, fragment
) -> None:
    admin = await superadmin_headers(client, seeded)
    advisor.error = error
    response = await client.post("/admin/advisor/ask", json={"question": "¿Hola?"}, headers=admin)
    assert response.status_code == 502 and fragment in response.json()["detail"]

    history = (await client.get("/admin/advisor/history", headers=admin)).json()
    assert [(h["status"], h["answer"]) for h in history] == [("error", None)]
    assert fragment in history[0]["error"]


@pytest.mark.ac("AC-007-6")
@pytest.mark.parametrize("body", [{"question": ""}, {"question": "x" * 1001}, {}, {"question": 5}])
async def test_pregunta_invalida_da_422_sin_llamar_a_la_ia(
    client: httpx.AsyncClient, seeded, advisor: FakeAdvisor, body
) -> None:
    admin = await superadmin_headers(client, seeded)
    assert (await client.post("/admin/advisor/ask", json=body, headers=admin)).status_code == 422
    assert advisor.prompts == []
    assert (
        await client.post("/admin/advisor/ask", json={"question": "   "}, headers=admin)
    ).status_code == 422
    assert advisor.prompts == []


@pytest.mark.ac("AC-007-7")
async def test_historial_mas_reciente_primero(client: httpx.AsyncClient, seeded) -> None:
    admin = await superadmin_headers(client, seeded)
    for question in ("primera", "segunda", "tercera"):
        await client.post("/admin/advisor/ask", json={"question": question}, headers=admin)
    history = (await client.get("/admin/advisor/history", headers=admin)).json()
    assert [h["question"] for h in history] == ["tercera", "segunda", "primera"]
    assert all(h["status"] == "ok" and h["answer"] for h in history)
