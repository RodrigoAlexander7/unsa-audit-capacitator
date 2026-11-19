"""Tests de integracion de F8: hechos UNSA enriquecidos, referencia, audit_checklist y guia."""

from datetime import date
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import text

from tests.integration.conftest import register_and_login, solve_module
from tests.solutions import solve, wrong
from tests.unit.test_document_exercises import DOCUMENT_FORM_ALCANCE
from unsa_audit.learning.application.generators import generate_spec
from unsa_audit.learning.domain.route import ExerciseDef, ExerciseKind, Module
from unsa_audit.learning.infrastructure.learning_facts import LearningFacts
from unsa_audit.learning.infrastructure.sqlalchemy_repository import SqlAlchemyLearningRepository
from unsa_audit.learning.infrastructure.sqlalchemy_university_facts import (
    SqlAlchemyUniversityFacts,
)

pytestmark = pytest.mark.integration


@pytest.mark.ac("AC-009-11")
async def test_learning_facts_expone_hechos_enriquecidos_desde_postgres(seeded) -> None:
    facts = await LearningFacts(
        SqlAlchemyUniversityFacts(seeded.state.session_factory),
        seeded.state.get_pims_completeness,
    ).snapshot()
    assert any(p.unit_code == "OTI" and p.unit_name for p in facts.positions)
    assert any("datos de salud" in s.data_categories and s.owner_unit_code for s in facts.systems)
    assert len(facts.activities) == 10
    assert any(a.org_unit_code == "OBU" for a in facts.activities)
    assert all(p.expected_evidence and p.summary for p in facts.pims)


@pytest.mark.ac("AC-009-10")
async def test_modulo_r3_devuelve_ejemplo_resuelto_y_sin_claves_privadas(
    client: httpx.AsyncClient, seeded
) -> None:
    headers = await register_and_login(client)
    # Completar R1 y R2 para matricular en R3
    for code in ("sensibilizacion", "interpretacion"):
        assert (await client.post(f"/routes/{code}/enroll", headers=headers)).status_code == 201
        detail = (await client.get(f"/routes/{code}", headers=headers)).json()
        for m in detail["modules"]:
            if m["planned"]:
                continue
            if m["has_exercise"]:
                ans = await solve_module(seeded, m["id"])
                resp = await client.post(
                    f"/modules/{m['id']}/attempts", json={"answer": ans}, headers=headers
                )
                assert resp.status_code == 200
            else:
                assert (
                    await client.post(f"/modules/{m['id']}/complete", headers=headers)
                ).status_code == 200

    assert (await client.post("/routes/implementacion/enroll", headers=headers)).status_code == 201
    r3 = (await client.get("/routes/implementacion", headers=headers)).json()
    soa_summary = next(m for m in r3["modules"] if m["order"] == 4)

    mod_resp = await client.get(f"/modules/{soa_summary['id']}", headers=headers)
    assert mod_resp.status_code == 200
    body = mod_resp.json()
    assert body["reference"] is not None
    assert "Biblioteca Central" in body["reference"]["title"]
    assert "Biblioteca Digital" in body["reference"]["body_md"]
    assert "applies" not in str(body["exercise"])


@pytest.mark.ac("AC-009-6")
@pytest.mark.ac("AC-009-9")
async def test_document_form_y_audit_checklist_dinamico_por_api(
    client: httpx.AsyncClient, seeded
) -> None:
    headers = await register_and_login(client)
    assert (await client.post("/routes/sensibilizacion/enroll", headers=headers)).status_code == 201

    repo = SqlAlchemyLearningRepository(seeded.state.session_factory)
    routes = await repo.list_routes()
    existing = await repo.list_modules()

    doc_mod = Module(
        id=uuid4(),
        route_code="sensibilizacion",
        slug="piloto-alcance-doc",
        order=90,
        title="Piloto alcance PIMS",
        minutes=10,
        mandatory=False,
        is_final=False,
        lesson_md="# Lección piloto",
        exercise=ExerciseDef(ExerciseKind.DOCUMENT_FORM, DOCUMENT_FORM_ALCANCE, pass_score=70),
        reference_title="Alcance UNSA",
        reference_md="# Referencia\nAlcance base.",
    )
    chk_mod = Module(
        id=uuid4(),
        route_code="sensibilizacion",
        slug="piloto-checklist-pims",
        order=91,
        title="Piloto checklist PIMS",
        minutes=10,
        mandatory=False,
        is_final=False,
        lesson_md="# Lección checklist",
        exercise=ExerciseDef(
            ExerciseKind.AUDIT_CHECKLIST,
            generator="audit_checklist_from_pims",
            params={},
            pass_score=70,
        ),
    )
    await repo.replace_content(routes, [*existing, doc_mod, chk_mod])

    # 1) Guia progresiva al 3er fallo en document_form
    get_doc = await client.get(f"/modules/{doc_mod.id}", headers=headers)
    assert get_doc.status_code == 200
    assert "cross_rules" not in str(get_doc.json()["exercise"])

    bad_ans = wrong(ExerciseKind.DOCUMENT_FORM)
    for expected_n, expected_reveal in ((1, False), (2, False), (3, True)):
        attempt = await client.post(
            f"/modules/{doc_mod.id}/attempts", json={"answer": bad_ans}, headers=headers
        )
        assert attempt.status_code == 200
        payload = attempt.json()
        assert payload["attempt_number"] == expected_n
        assert payload["passed"] is False
        assert payload["solution_revealed"] is expected_reveal
        if expected_reveal:
            assert payload["solution_guide"] and len(payload["solution_guide"]) > 0
        else:
            assert payload["solution_guide"] is None

    perfect_doc = solve(ExerciseKind.DOCUMENT_FORM, DOCUMENT_FORM_ALCANCE)
    ok_resp = await client.post(
        f"/modules/{doc_mod.id}/attempts", json={"answer": perfect_doc}, headers=headers
    )
    assert ok_resp.status_code == 200 and ok_resp.json()["passed"] is True

    # 2) audit_checklist generado desde BD reacciona cuando pims-soa pasa a vigente
    facts = LearningFacts(
        SqlAlchemyUniversityFacts(seeded.state.session_factory),
        seeded.state.get_pims_completeness,
    )
    spec_before = generate_spec("audit_checklist_from_pims", {}, await facts.snapshot())
    ans_before = solve(ExerciseKind.AUDIT_CHECKLIST, spec_before)
    assert (
        await client.post(
            f"/modules/{chk_mod.id}/attempts", json={"answer": ans_before}, headers=headers
        )
    ).json()["score"] == 100

    async with seeded.state.session_factory() as session, session.begin():
        await session.execute(
            text("UPDATE documents SET lifecycle='in_force', review_date=:d WHERE code='pims-soa'"),
            {"d": date(2030, 12, 31)},
        )

    res_after = (
        await client.post(
            f"/modules/{chk_mod.id}/attempts", json={"answer": ans_before}, headers=headers
        )
    ).json()
    assert res_after["score"] < 100
    soa_fb = next(i for i in res_after["items"] if i["id"] == "pims-soa")
    assert not soa_fb["correct"]
