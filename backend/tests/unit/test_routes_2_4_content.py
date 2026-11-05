"""AC-006-1/4/6: estructura y demos de las Rutas 2-4."""

from pathlib import Path

import pytest

from tests.solutions import solve
from tests.unit.fakes_learning import snapshot_from_dataset
from unsa_audit.documents.infrastructure.content_loader import FilePimsRequirementSource
from unsa_audit.learning.application.generators import generate_spec
from unsa_audit.learning.domain.exercises import grade, to_public, validate_spec
from unsa_audit.learning.domain.route import ExerciseKind
from unsa_audit.learning.infrastructure.content_loader import FileContentSource

CONTENT = Path(__file__).resolve().parents[3] / "content"


@pytest.fixture(scope="module")
def loaded():
    routes, modules = FileContentSource(CONTENT).load()
    return {r.code: r for r in routes}, modules


def _modules(loaded, code):
    return [m for m in loaded[1] if m.route_code == code]


@pytest.mark.ac("AC-006-1")
@pytest.mark.parametrize(
    ("code", "count", "minutes"),
    [("implementacion", 9, 1440), ("auditor", 10, 1920)],
)
def test_estructura_completa_con_un_unico_modulo_publicado(loaded, code, count, minutes) -> None:
    modules = _modules(loaded, code)
    assert len(modules) == count and sum(m.minutes for m in modules) == minutes
    assert [m.order for m in modules] == list(range(1, count + 1))
    published = [m for m in modules if not m.planned]
    assert len(published) == 1
    demo = published[0]
    assert demo.mandatory and demo.exercise is not None and demo.minutes >= 120
    for planned in (m for m in modules if m.planned):
        assert not planned.mandatory and planned.exercise is None
        assert planned.lesson_md.startswith("# ")


@pytest.mark.ac("AC-010-1")
@pytest.mark.ac("AC-010-3")
@pytest.mark.ac("AC-010-4")
@pytest.mark.ac("AC-010-5")
@pytest.mark.ac("AC-010-6")
def test_ruta_2_completa_sin_planned_con_16_horas_y_referencias(loaded) -> None:
    modules = _modules(loaded, "interpretacion")
    assert len(modules) == 8
    assert sum(m.minutes for m in modules) == 960
    assert [m.order for m in modules] == list(range(1, 9))
    assert all(not m.planned and m.mandatory and m.exercise is not None for m in modules)
    assert modules[-1].is_final and not any(m.is_final for m in modules[:-1])

    for m in modules:
        assert m.reference_title and m.reference_md, f"{m.slug}: falta ejemplo resuelto"
        ex = m.exercise
        assert ex is not None
        validate_spec(ex.kind, ex.spec)
        public = to_public(ex.kind, ex.spec, "r2-test")
        for secret in ('"correct"', '"pairs"', '"rubric"', '"cross_rules"', '"sample_solution"'):
            assert secret not in str(public), f"{m.slug}: filtración {secret}"
        ans = solve(ex.kind, ex.spec)
        assert grade(ex.kind, ex.spec, ans).score == 100, f"{m.slug}: solve() no alcanza 100"


@pytest.mark.ac("AC-006-1")
def test_los_demos_son_los_previstos(loaded) -> None:
    demos = {
        code: next(m for m in _modules(loaded, code) if not m.planned)
        for code in ("implementacion", "auditor")
    }
    assert demos["implementacion"].exercise.kind is ExerciseKind.SOA_FORM
    assert demos["auditor"].exercise.generator == "pims_audit_findings"
    assert [demos[c].minutes for c in demos] == [180, 240]


@pytest.mark.ac("AC-006-4")
@pytest.mark.ac("AC-010-2")
def test_demo_de_interpretacion_usa_requisitos_pims_reales(loaded) -> None:
    mod6 = next(
        m for m in _modules(loaded, "interpretacion") if m.slug == "del-requisito-al-documento"
    )
    spec = mod6.exercise.spec
    validate_spec(ExerciseKind.MATCHING, spec)
    requirements = {r.code: r for r in FilePimsRequirementSource(CONTENT).load()}
    right = {o["id"]: o["label"] for o in spec["right"]}
    assert set(right) == set(requirements), "las 11 opciones son los 11 requisitos"
    for code, label in right.items():
        r = requirements[code]
        assert label.startswith(r.clause_ref + " "), f"{code}: la clausula no coincide"
    assert set(spec["pairs"].values()) <= set(requirements)
    assert grade(ExerciseKind.MATCHING, spec, solve(ExerciseKind.MATCHING, spec)).score == 100


@pytest.mark.ac("AC-006-6")
def test_demo_de_implementacion_es_resoluble_y_da_credito_parcial(loaded) -> None:
    demo = next(m for m in _modules(loaded, "implementacion") if not m.planned)
    spec = demo.exercise.spec
    validate_spec(ExerciseKind.SOA_FORM, spec)
    assert len(spec["controls"]) == 8
    perfect = solve(ExerciseKind.SOA_FORM, spec)
    assert grade(ExerciseKind.SOA_FORM, spec, perfect).score == 100

    # acierta todo menos la justificacion de 4 controles -> 75 %
    answer = {"decisions": {k: dict(v) for k, v in perfect["decisions"].items()}}
    for control_id in list(answer["decisions"])[:4]:
        answer["decisions"][control_id]["reason"] = "r-terceros-x"
    assert grade(ExerciseKind.SOA_FORM, spec, answer).score == 75
    assert 70 <= 75, "con 4 justificaciones erradas aun aprueba"

    public = to_public(ExerciseKind.SOA_FORM, spec, "s")
    assert "applies" not in str(public) and "explanation" not in str(public)


@pytest.mark.ac("AC-006-7")
def test_el_demo_de_auditoria_es_resoluble_con_los_datos_sembrados(loaded) -> None:
    demo = next(m for m in _modules(loaded, "auditor") if not m.planned)
    spec = generate_spec(demo.exercise.generator, demo.exercise.params, snapshot_from_dataset())
    validate_spec(ExerciseKind.MATCHING, spec)
    assert len(spec["left"]) == 11
    assert grade(ExerciseKind.MATCHING, spec, solve(ExerciseKind.MATCHING, spec)).score == 100
