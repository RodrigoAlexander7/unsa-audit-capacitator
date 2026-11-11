from dataclasses import replace

import pytest

from tests.solutions import solve
from tests.unit.fakes_learning import snapshot_from_dataset
from unsa_audit.learning.application.generators import generate_spec
from unsa_audit.learning.application.ports import UniversitySnapshot
from unsa_audit.learning.domain.exercises import (
    InvalidExerciseSpec,
    grade,
    to_public,
    validate_spec,
)
from unsa_audit.learning.domain.route import ExerciseKind

CASES = [
    {"text": "Se extravió un acta.", "unit_code": "ORA"},
    {"text": "No entra al aula virtual.", "unit_code": "OTI"},
    {"text": "Error en planilla.", "unit_code": "ORH"},
    {"text": "Caso con unidad inexistente.", "unit_code": "XXX"},
]


@pytest.mark.ac("AC-003-9")
def test_org_levels_clasifica_cargos_segun_la_bd() -> None:
    spec = generate_spec("org_levels", {"per_kind": 2}, snapshot_from_dataset())
    validate_spec(ExerciseKind.MATCHING, spec)
    titles = {i["id"]: i["label"] for i in spec["left"]}
    by_title = {v: spec["pairs"][k] for k, v in titles.items()}
    assert by_title["Rector"] == "rectorado"
    assert by_title["Vicerrector Académico"] == "vicerrectorado"
    assert {r["id"] for r in spec["right"]} == {
        "rectorado", "vicerrectorado", "facultad", "escuela", "oficina",
    }  # fmt: skip
    assert grade(ExerciseKind.MATCHING, spec, solve(ExerciseKind.MATCHING, spec)).score == 100


@pytest.mark.ac("AC-003-9")
def test_responsibility_cases_usa_nombres_de_unidades_de_la_bd() -> None:
    snap = snapshot_from_dataset()
    spec = generate_spec("responsibility_cases", {"cases": CASES, "distractors": 3}, snap)
    validate_spec(ExerciseKind.QUIZ, spec)
    assert len(spec["questions"]) == 3, "el caso con unidad inexistente se omite"
    first = spec["questions"][0]
    names = {u.code: u.name for u in snap.units}
    assert {o["label"] for o in first["options"]} >= {names["ORA"]}
    assert len(first["options"]) == 4
    assert first["correct"] == "ORA"


@pytest.mark.ac("AC-003-9")
def test_los_distractores_no_siempre_dejan_la_correcta_en_la_misma_posicion() -> None:
    spec = generate_spec("responsibility_cases", {"cases": CASES[:3], "distractors": 3},
                         snapshot_from_dataset())  # fmt: skip
    positions = {[o["id"] for o in q["options"]].index(q["correct"]) for q in spec["questions"]}
    assert len(positions) > 1


@pytest.mark.ac("AC-003-9")
def test_cambiar_un_dato_de_la_bd_cambia_el_ejercicio_y_su_solucion() -> None:
    snap = snapshot_from_dataset()
    renamed = replace(
        snap,
        units=[replace(u, name="Oficina Renombrada") if u.code == "ORA" else u for u in snap.units],
        systems=[
            replace(s, owner_unit_name="Oficina Renombrada")
            if s.owner_unit_name == "Oficina de Registros Académicos" else s
            for s in snap.systems
        ],
    )  # fmt: skip
    spec = generate_spec("system_owners", {"limit": 8}, renamed)
    assert "Oficina Renombrada" in {r["label"] for r in spec["right"]}
    assert grade(ExerciseKind.MATCHING, spec, solve(ExerciseKind.MATCHING, spec)).score == 100
    public = to_public(ExerciseKind.MATCHING, spec, "m4")
    assert "pairs" not in public


@pytest.mark.ac("AC-003-9")
def test_generadores_fallan_con_claridad_si_faltan_datos() -> None:
    empty = UniversitySnapshot()
    for name in ("org_levels", "system_owners"):
        with pytest.raises(InvalidExerciseSpec):
            generate_spec(name, {}, empty)
    with pytest.raises(InvalidExerciseSpec):
        generate_spec("responsibility_cases", {"cases": CASES}, empty)
    with pytest.raises(InvalidExerciseSpec):
        generate_spec("no-existe", {}, empty)
