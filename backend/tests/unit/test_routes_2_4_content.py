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


@pytest.mark.ac("AC-010-1")
@pytest.mark.ac("AC-011-1")
@pytest.mark.ac("AC-012-1")
def test_todas_las_rutas_completas_suman_84_horas_sin_modulos_planned(loaded) -> None:
    routes, modules = loaded
    assert [(r.code, r.hours) for r in sorted(routes.values(), key=lambda r: r.order)] == [
        ("sensibilizacion", 12),
        ("interpretacion", 16),
        ("implementacion", 24),
        ("auditor", 32),
    ]
    assert not any(m.planned for m in modules), "ya no deben quedar modulos planned"


@pytest.mark.ac("AC-010-1")
@pytest.mark.ac("AC-011-1")
@pytest.mark.ac("AC-012-1")
@pytest.mark.parametrize(
    ("code", "count", "minutes"),
    [("interpretacion", 8, 960), ("implementacion", 9, 1440), ("auditor", 10, 1920)],
)
def test_rutas_2_a_4_completas_validas_y_resolubles(loaded, code, count, minutes) -> None:
    modules = _modules(loaded, code)
    assert len(modules) == count
    assert sum(m.minutes for m in modules) == minutes
    assert [m.order for m in modules] == list(range(1, count + 1))
    assert all(not m.planned and m.mandatory and m.exercise is not None for m in modules)
    assert modules[-1].is_final and not any(m.is_final for m in modules[:-1])

    snap = snapshot_from_dataset()
    for m in modules:
        assert m.reference_title and m.reference_md, f"{m.slug}: falta ejemplo resuelto"
        ex = m.exercise
        assert ex is not None
        spec = generate_spec(ex.generator, ex.params, snap) if ex.generator else ex.spec
        validate_spec(ex.kind, spec)
        public = to_public(ex.kind, spec, f"{code}-test")
        for secret in (
            '"correct"',
            '"pairs"',
            '"rubric"',
            '"cross_rules"',
            '"sample_solution"',
            '"expected_',
        ):
            assert secret not in str(public), f"{m.slug}: filtración {secret}"
        ans = solve(ex.kind, spec)
        assert grade(ex.kind, spec, ans).score == 100, f"{m.slug}: solve() no alcanza 100"


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
@pytest.mark.ac("AC-011-2")
def test_demo_de_implementacion_es_resoluble_y_da_credito_parcial(loaded) -> None:
    demo = next(
        m for m in _modules(loaded, "implementacion") if m.slug == "declaracion-de-aplicabilidad"
    )
    spec = demo.exercise.spec
    validate_spec(ExerciseKind.SOA_FORM, spec)
    assert len(spec["controls"]) == 8
    perfect = solve(ExerciseKind.SOA_FORM, spec)
    assert grade(ExerciseKind.SOA_FORM, spec, perfect).score == 100

    answer = {"decisions": {k: dict(v) for k, v in perfect["decisions"].items()}}
    for control_id in list(answer["decisions"])[:4]:
        answer["decisions"][control_id]["reason"] = "r-terceros-x"
    assert grade(ExerciseKind.SOA_FORM, spec, answer).score == 75

    public = to_public(ExerciseKind.SOA_FORM, spec, "s")
    assert "applies" not in str(public) and "explanation" not in str(public)


@pytest.mark.ac("AC-006-7")
@pytest.mark.ac("AC-012-2")
def test_el_demo_de_auditoria_es_resoluble_con_los_datos_sembrados(loaded) -> None:
    demo = next(m for m in _modules(loaded, "auditor") if m.slug == "simulacion-auditar-el-pims")
    spec = generate_spec(demo.exercise.generator, demo.exercise.params, snapshot_from_dataset())
    validate_spec(ExerciseKind.MATCHING, spec)
    assert len(spec["left"]) == 11
    assert grade(ExerciseKind.MATCHING, spec, solve(ExerciseKind.MATCHING, spec)).score == 100
