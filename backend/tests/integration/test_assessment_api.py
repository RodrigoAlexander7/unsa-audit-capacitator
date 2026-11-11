import httpx
import pytest

from tests.integration.conftest import register_and_login

pytestmark = pytest.mark.integration

LEAK = {"correct", "explanation", "competency", "requirement"}


async def _start(client, headers, profile="controller"):
    return await client.post("/assessments", json={"profile": profile}, headers=headers)


def _answers(attempt: dict, correct: dict[str, str] | None = None) -> dict[str, str]:
    """Responde 'a' a todo salvo lo indicado (id de pregunta -> opcion)."""
    answers = {q["id"]: q["options"][0]["id"] for q in attempt["questions"]}
    return answers | (correct or {})


async def _truth(app, profile: str) -> dict[str, str]:
    from unsa_audit.assessment.domain.assessment import Profile

    definition = app.state.start_assessment._bank.get(Profile(profile))
    return {q.id: q.correct for q in definition.questions}


@pytest.mark.ac("AC-006-10")
async def test_iniciar_devuelve_12_preguntas_publicas_en_orden_por_intento(
    client: httpx.AsyncClient, seeded
) -> None:
    headers = await register_and_login(client)
    first = await _start(client, headers)
    second = await _start(client, headers)
    assert first.status_code == 201
    body = first.json()
    assert body["profile"] == "controller" and body["status"] == "in_progress"
    assert len(body["questions"]) == 12 and body["pass_score"] == 70
    assert body["result"] is None and body["score"] is None
    for question in body["questions"]:
        assert not LEAK & set(question), question
        assert all(set(o) == {"id", "label"} for o in question["options"])
    ids = lambda b: [q["id"] for q in b["questions"]]  # noqa: E731
    assert sorted(ids(body)) == sorted(ids(second.json()))
    assert ids(body) != ids(second.json()), "cada intento tiene su propio orden"
    assert ids((await client.get(f"/assessments/{body['id']}", headers=headers)).json()) == ids(
        body
    )

    processor = await _start(client, headers, "processor")
    assert processor.status_code == 201 and processor.json()["profile"] == "processor"


@pytest.mark.ac("AC-006-10")
async def test_perfil_invalido_y_sin_autenticacion(client: httpx.AsyncClient, seeded) -> None:
    headers = await register_and_login(client)
    assert (await _start(client, headers, "auditor")).status_code == 422
    assert (await client.post("/assessments", json={})).status_code == 401
    assert (await client.post("/assessments", json={"profile": "controller"})).status_code == 401
    assert (await client.get("/assessments")).status_code == 401


@pytest.mark.ac("AC-006-11")
async def test_enviar_corrige_y_calcula_competencias_y_requisitos(
    client: httpx.AsyncClient, seeded
) -> None:
    headers = await register_and_login(client)
    attempt = (await _start(client, headers)).json()
    truth = await _truth(seeded, "controller")

    response = await client.post(
        f"/assessments/{attempt['id']}/submit",
        json={"answers": truth},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert (body["status"], body["score"], body["passed"]) == ("finished", 100, True)
    assert body["questions"] == [], "una vez enviada ya no se devuelven las preguntas"
    result = body["result"]
    assert result["score"] == 100 and result["pass_score"] == 70
    assert sum(g["total"] for g in result["competencies"]) == 12
    assert all(g["percent"] == 100 for g in result["competencies"] + result["requirements"])
    assert {g["key"] for g in result["competencies"]} >= {"brechas", "encargados"}
    labels = {g["label"] for g in result["requirements"]}
    assert any(label.startswith("6.1.3 c ") for label in labels), "etiqueta con clausula y titulo"
    assert len(result["items"]) == 12 and all(i["correct"] for i in result["items"])


@pytest.mark.ac("AC-006-11")
@pytest.mark.ac("AC-006-13")
async def test_resultado_parcial_sin_responder_y_no_aprobado(
    client: httpx.AsyncClient, seeded
) -> None:
    headers = await register_and_login(client)
    attempt = (await _start(client, headers, "processor")).json()
    truth = await _truth(seeded, "processor")
    wrong_all = {q["id"]: "zzz" for q in attempt["questions"]}
    first_four = {qid: truth[qid] for qid in list(truth)[:4]}  # solo 4 correctas

    response = await client.post(
        f"/assessments/{attempt['id']}/submit",
        json={"answers": wrong_all | first_four | {"id-desconocido": "a"}},
        headers=headers,
    )
    body = response.json()
    assert (body["score"], body["passed"]) == (33, False)
    result = body["result"]
    assert sum(i["correct"] for i in result["items"]) == 4
    unanswered = next(i for i in result["items"] if not i["correct"])
    assert unanswered["chosen_label"] is None and unanswered["explanation"]
    assert unanswered["correct_label"]

    empty = await _start(client, headers)
    zero = await client.post(
        f"/assessments/{empty.json()['id']}/submit", json={"answers": {}}, headers=headers
    )
    assert zero.json()["score"] == 0


@pytest.mark.ac("AC-006-11")
async def test_no_se_envia_dos_veces_y_solo_el_dueno_ve_el_intento(
    client: httpx.AsyncClient, seeded
) -> None:
    owner = await register_and_login(client)
    stranger = await register_and_login(client, "otra@example.com")
    attempt = (await _start(client, owner)).json()
    url = f"/assessments/{attempt['id']}"

    assert (await client.get(url, headers=stranger)).status_code == 404
    assert (
        await client.post(f"{url}/submit", json={"answers": {}}, headers=stranger)
    ).status_code == 404

    assert (
        await client.post(f"{url}/submit", json={"answers": {}}, headers=owner)
    ).status_code == 200
    again = await client.post(f"{url}/submit", json={"answers": {}}, headers=owner)
    assert again.status_code == 409
    missing = "00000000-0000-0000-0000-000000000000"
    assert (await client.get(f"/assessments/{missing}", headers=owner)).status_code == 404


@pytest.mark.ac("AC-006-13")
async def test_respuestas_con_forma_invalida_dan_422_y_no_consumen_el_intento(
    client: httpx.AsyncClient, seeded
) -> None:
    headers = await register_and_login(client)
    attempt = (await _start(client, headers)).json()
    url = f"/assessments/{attempt['id']}/submit"
    for body in ({"answers": "texto"}, {"answers": ["a"]}, {"answers": {"q": 3}}, {}):
        assert (await client.post(url, json=body, headers=headers)).status_code == 422
    still = (await client.get(f"/assessments/{attempt['id']}", headers=headers)).json()
    assert still["status"] == "in_progress" and len(still["questions"]) == 12
    assert (await client.post(url, json={"answers": {}}, headers=headers)).status_code == 200


@pytest.mark.ac("AC-006-12")
async def test_listado_de_mis_intentos_y_resultado_posterior(
    client: httpx.AsyncClient, seeded
) -> None:
    headers = await register_and_login(client)
    other = await register_and_login(client, "otra@example.com")
    await _start(client, other)
    first = (await _start(client, headers)).json()
    second = (await _start(client, headers, "processor")).json()
    truth = await _truth(seeded, "controller")
    await client.post(
        f"/assessments/{first['id']}/submit", json={"answers": truth}, headers=headers
    )

    listing = (await client.get("/assessments", headers=headers)).json()
    assert [a["id"] for a in listing] == [second["id"], first["id"]], "mas recientes primero"
    assert [(a["profile"], a["status"], a["score"]) for a in listing] == [
        ("processor", "in_progress", None),
        ("controller", "finished", 100),
    ]
    assert listing[1]["finished_at"] and listing[1]["passed"] is True

    stored = (await client.get(f"/assessments/{first['id']}", headers=headers)).json()
    assert stored["result"]["score"] == 100 and stored["title"].startswith("Evaluación")
