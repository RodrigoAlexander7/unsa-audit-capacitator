from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from tests.solutions import solve, wrong
from tests.unit.fakes_learning import FakeFacts, InMemoryLearningRepository, pims_facts
from unsa_audit.learning.application.errors import ModulePlanned
from unsa_audit.learning.application.generators import generate_spec
from unsa_audit.learning.application.ports import UniversitySnapshot
from unsa_audit.learning.application.use_cases import (
    EnrollInRoute,
    GetModule,
    GetRoute,
    ListRoutes,
    SubmitAttempt,
)
from unsa_audit.learning.domain.exercises import (
    InvalidAnswer,
    InvalidExerciseSpec,
    grade,
    to_public,
    validate_spec,
)
from unsa_audit.learning.domain.progress import module_status, route_completed
from unsa_audit.learning.domain.route import (
    ExerciseDef,
    ExerciseKind,
    Module,
    ModuleStatus,
    Route,
    RouteStatus,
)
from unsa_audit.learning.infrastructure.content_loader import ContentError, FileContentSource

CONTENT = Path(__file__).resolve().parents[3] / "content"
NOW = datetime(2026, 1, 1, tzinfo=UTC)

SOA = {
    "prompt": "Completa",
    "scenario": "Una oficina que usa un proveedor.",
    "reasons": [{"id": "r1", "label": "Rol responsable"}, {"id": "r2", "label": "Sin sensibles"}],
    "controls": [
        {"id": "c1", "label": "Finalidad", "applies": True, "reason": "r1", "explanation": "E1"},
        {"id": "c2", "label": "Salud", "applies": False, "reason": "r2", "explanation": "E2"},
    ],
}


# ---------------------------------------------------------------------------- soa_form


@pytest.mark.ac("AC-006-5")
def test_soa_form_valida_publica_y_corrige_con_credito_parcial() -> None:
    validate_spec(ExerciseKind.SOA_FORM, SOA)
    perfect = solve(ExerciseKind.SOA_FORM, SOA)
    assert grade(ExerciseKind.SOA_FORM, SOA, perfect).score == 100

    only_applicability = {"decisions": {"c1": {"applies": True, "reason": "r2"},
                                        "c2": {"applies": False, "reason": "r1"}}}  # fmt: skip
    partial = grade(ExerciseKind.SOA_FORM, SOA, only_applicability)
    assert partial.score == 50
    assert [i.correct for i in partial.items] == [False, False]

    half_right = {"decisions": {"c1": {"applies": True, "reason": "r1"}}}  # c2 sin responder
    result = grade(ExerciseKind.SOA_FORM, SOA, half_right)
    assert result.score == 50 and [i.correct for i in result.items] == [True, False]
    assert result.items[1].feedback == "E2"
    assert grade(ExerciseKind.SOA_FORM, SOA, wrong(ExerciseKind.SOA_FORM)).score == 0


@pytest.mark.ac("AC-006-5")
def test_soa_form_publico_no_filtra_la_solucion() -> None:
    public = to_public(ExerciseKind.SOA_FORM, SOA, "semilla")
    assert set(public) == {"prompt", "scenario", "reasons", "controls"}
    assert all(set(c) == {"id", "label"} for c in public["controls"])
    assert "explanation" not in str(public) and "applies" not in str(public)


@pytest.mark.ac("AC-006-5")
@pytest.mark.parametrize(
    "answer",
    [
        {"decisions": "x"},
        {"decisions": {"c1": "si"}},
        {"decisions": {"c1": {"applies": "yes", "reason": "r1"}}},
        {"decisions": {"c1": {"applies": True, "reason": 3}}},
        {},
        "texto",
    ],
)
def test_soa_form_respuestas_invalidas(answer: object) -> None:
    with pytest.raises(InvalidAnswer):
        grade(ExerciseKind.SOA_FORM, SOA, answer)


@pytest.mark.ac("AC-006-5")
@pytest.mark.parametrize(
    "broken",
    [
        {**SOA, "scenario": ""},
        {**SOA, "controls": []},
        {**SOA, "controls": [{**SOA["controls"][0], "reason": "zzz"}]},
        {**SOA, "controls": [{**SOA["controls"][0], "applies": "si"}]},
        {**SOA, "controls": [{**SOA["controls"][0], "explanation": ""}]},
        {**SOA, "controls": [SOA["controls"][0], SOA["controls"][0]]},
    ],
)
def test_soa_form_spec_rota(broken: dict) -> None:
    with pytest.raises(InvalidExerciseSpec):
        validate_spec(ExerciseKind.SOA_FORM, broken)


# ---------------------------------------------------------------------------- generador de auditoria

S = "in_force"


@pytest.mark.ac("AC-006-7")
def test_pims_audit_findings_clasifica_segun_el_estado_real() -> None:
    facts = UniversitySnapshot(pims=pims_facts())
    spec = generate_spec("pims_audit_findings", {}, facts)
    validate_spec(ExerciseKind.MATCHING, spec)
    by_clause = {f.clause_ref: f for f in facts.pims}
    expected = {  # estado sembrado a 2026-11-11 -> hallazgo
        "4.3": "conforme", "5.2": "conforme", "6.1.3 c": "conforme", "8.2": "conforme",
        "7.2": "conforme", "6.1.2": "no_conformidad", "10.2": "no_conformidad",
        "6.1.3 e": "no_conformidad", "8.3": "no_conformidad", "9.1": "no_conformidad",
        "6.1.3 f": "observacion",
    }  # fmt: skip
    assert {c: spec["pairs"][by_clause[c].code] for c in expected} == expected
    assert {r["id"] for r in spec["right"]} == {"conforme", "observacion", "no_conformidad"}
    texts = {i["id"]: i["label"] for i in spec["left"]}
    assert "No existe ningún documento" in texts["pims-monitoreo"]
    assert (
        "borrador" in texts["pims-soa"]
        and "no tiene unidad responsable" in texts["pims-plan-tratamiento"]
    )
    assert grade(ExerciseKind.MATCHING, spec, solve(ExerciseKind.MATCHING, spec)).score == 100


@pytest.mark.ac("AC-006-7")
def test_el_ejercicio_de_auditoria_cambia_si_cambia_el_estado() -> None:
    before = generate_spec("pims_audit_findings", {}, UniversitySnapshot(pims=pims_facts()))
    # con el tiempo los vigentes vencen: todo lo vigente pasa a no conformidad
    later = generate_spec(
        "pims_audit_findings",
        {},
        UniversitySnapshot(pims=pims_facts(today=__import__("datetime").date(2031, 1, 1))),
    )
    assert before["pairs"] != later["pairs"]
    assert list(later["pairs"].values()).count("conforme") == 0
    with pytest.raises(InvalidExerciseSpec):
        generate_spec("pims_audit_findings", {}, UniversitySnapshot())


# ---------------------------------------------------------------------------- modulos planned


def _module(order: int, *, planned: bool = False, mandatory: bool = True, exercise: bool = False):
    ex = ExerciseDef(ExerciseKind.SINGLE_CHOICE, {
        "prompt": "p", "options": [{"id": "a", "label": "A"}, {"id": "b", "label": "B"}],
        "correct": "a"}) if exercise else None  # fmt: skip
    return Module(uuid4(), "r1", f"m{order}", order, f"M{order}", 60, mandatory, False, "# L", ex,
                  planned=planned)  # fmt: skip


@pytest.mark.ac("AC-006-2")
def test_un_modulo_planned_siempre_esta_bloqueado_y_no_cuenta_para_completar() -> None:
    demo, planned = _module(1, exercise=True), _module(2, planned=True, mandatory=False)
    mods = [planned, demo]
    assert module_status(planned, mods, set(), enrolled=True) is ModuleStatus.LOCKED
    assert module_status(demo, mods, set(), enrolled=True) is ModuleStatus.AVAILABLE
    assert route_completed(mods, {demo.id}) is True
    assert route_completed([planned], set()) is False, "solo modulos planned: nunca se completa"
    assert route_completed([], set()) is False


@pytest.fixture
def planned_repo():
    route = Route("r1", 1, "R1", "", 3, None)
    demo, planned = _module(2, exercise=True), _module(1, planned=True, mandatory=False)
    return InMemoryLearningRepository([route], [planned, demo]), planned, demo


@pytest.mark.ac("AC-006-2")
async def test_planned_da_error_y_se_informa_aparte(planned_repo) -> None:
    repo, planned, demo = planned_repo
    user = uuid4()
    await EnrollInRoute(repo, clock=lambda: NOW).execute(user, "r1")
    with pytest.raises(ModulePlanned):
        await GetModule(repo, FakeFacts()).execute(user, planned.id)
    with pytest.raises(ModulePlanned):
        await SubmitAttempt(repo, FakeFacts(), clock=lambda: NOW).execute(user, planned.id, {})

    detail = await GetRoute(repo).execute(user, "r1")
    assert (detail.summary.modules_total, detail.summary.modules_planned) == (1, 1)
    assert [(m.module.planned, m.status) for m in detail.modules] == [
        (True, ModuleStatus.LOCKED), (False, ModuleStatus.AVAILABLE),
    ]  # fmt: skip


@pytest.mark.ac("AC-006-8")
async def test_aprobar_el_unico_modulo_obligatorio_completa_la_ruta(planned_repo) -> None:
    repo, _, demo = planned_repo
    user = uuid4()
    await EnrollInRoute(repo, clock=lambda: NOW).execute(user, "r1")
    result = await SubmitAttempt(repo, FakeFacts(), clock=lambda: NOW).execute(
        user, demo.id, {"choice": "a"}
    )
    assert result.module_completed and result.route_completed
    listing = await ListRoutes(repo).execute(user)
    summary = listing.routes[0]
    assert summary.status is RouteStatus.COMPLETED
    assert (summary.minutes_credited, summary.modules_completed, summary.modules_planned) == (
        60,
        1,
        1,
    )


@pytest.mark.ac("AC-006-1")
def test_un_modulo_planned_no_puede_tener_ejercicio_ni_ser_obligatorio(tmp_path: Path) -> None:
    route = tmp_path / "routes" / "1-x"
    route.mkdir(parents=True)
    (route / "route.yaml").write_text("code: x\norder: 1\ntitle: X\nhours: 1\n", encoding="utf-8")
    (route / "01-a.md").write_text(
        "---\ntitle: A\nminutes: 60\nplanned: true\nmandatory: true\n---\n# A\n", encoding="utf-8"
    )
    with pytest.raises(ContentError, match="planned"):
        FileContentSource(tmp_path).load()
    (route / "01-a.md").write_text("---\ntitle: A\nminutes: 60\nplanned: true\n---\n# A\n")
    assert FileContentSource(tmp_path).load()[1][0].planned is True
