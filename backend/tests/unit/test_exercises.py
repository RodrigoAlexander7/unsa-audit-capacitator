import pytest

from tests.solutions import solve, wrong
from unsa_audit.learning.domain.exercises import (
    InvalidAnswer,
    InvalidExerciseSpec,
    grade,
    to_public,
    validate_spec,
)
from unsa_audit.learning.domain.route import ExerciseKind

OPTIONS = [{"id": "a", "label": "A"}, {"id": "b", "label": "B"}, {"id": "c", "label": "C"}]

ORDERING = {
    "prompt": "Ordena",
    "items": [{"id": "x", "label": "X"}, {"id": "y", "label": "Y"},
              {"id": "z", "label": "Z"}, {"id": "w", "label": "W"}],
    "correct_order": ["x", "y", "z", "w"],
}  # fmt: skip
MATCHING = {
    "prompt": "Clasifica",
    "left": [{"id": "l1", "label": "L1"}, {"id": "l2", "label": "L2"},
             {"id": "l3", "label": "L3"}, {"id": "l4", "label": "L4"}],
    "right": [{"id": "r1", "label": "R1"}, {"id": "r2", "label": "R2"}],
    "pairs": {"l1": "r1", "l2": "r1", "l3": "r2", "l4": "r2"},
}  # fmt: skip
SINGLE = {"prompt": "Elige", "options": OPTIONS, "correct": "b", "explanation": "Porque B."}
QUIZ = {
    "prompt": "Quiz",
    "questions": [
        {"id": f"q{i}", "prompt": f"Pregunta {i}", "options": OPTIONS, "correct": "a",
         "explanation": f"E{i}"}
        for i in range(4)
    ],
}  # fmt: skip
BRANCHING = {
    "prompt": "Decide",
    "steps": [
        {"id": "s1", "situation": "Uno", "options": [
            {"id": "ok", "label": "Bien", "points": 10, "feedback": "Bien!"},
            {"id": "meh", "label": "Regular", "points": 5, "feedback": "Regular"},
            {"id": "mal", "label": "Mal", "points": 0, "feedback": "Mal"}]},
        {"id": "s2", "situation": "Dos", "options": [
            {"id": "ok", "label": "Bien", "points": 10, "feedback": "Bien!"},
            {"id": "mal", "label": "Mal", "points": 0, "feedback": "Mal"}]},
    ],
}  # fmt: skip

SPECS = {
    ExerciseKind.ORDERING: ORDERING,
    ExerciseKind.MATCHING: MATCHING,
    ExerciseKind.SINGLE_CHOICE: SINGLE,
    ExerciseKind.QUIZ: QUIZ,
    ExerciseKind.BRANCHING: BRANCHING,
}


@pytest.mark.ac("AC-003-7")
@pytest.mark.parametrize("kind", list(SPECS))
def test_respuesta_perfecta_100_y_vacia_menos_de_100(kind: ExerciseKind) -> None:
    validate_spec(kind, SPECS[kind])
    perfect = grade(kind, SPECS[kind], solve(kind, SPECS[kind]))
    assert perfect.score == 100
    assert all(i.correct for i in perfect.items)
    empty = grade(kind, SPECS[kind], wrong(kind))
    assert empty.score == 0
    assert not any(i.correct for i in empty.items)


@pytest.mark.ac("AC-003-7")
def test_ordering_puntua_por_posiciones_correctas() -> None:
    result = grade(ExerciseKind.ORDERING, ORDERING, {"order": ["x", "y", "w", "z"]})
    assert result.score == 50  # 2 de 4 en su sitio
    assert [i.correct for i in result.items] == [True, True, False, False]


@pytest.mark.ac("AC-003-7")
def test_matching_puntua_por_aciertos_e_ignora_ids_desconocidos() -> None:
    answer = {"assignments": {"l1": "r1", "l2": "r2", "l3": "r2", "l4": "no-existe", "zz": "r1"}}
    assert grade(ExerciseKind.MATCHING, MATCHING, answer).score == 50


@pytest.mark.ac("AC-003-7")
def test_quiz_porcentaje_de_aciertos() -> None:
    answers = {"q0": "a", "q1": "a", "q2": "b", "q3": "c"}
    result = grade(ExerciseKind.QUIZ, QUIZ, {"answers": answers})
    assert result.score == 50
    assert result.items[0].feedback == "E0"


@pytest.mark.ac("AC-003-7")
def test_single_choice_todo_o_nada_con_explicacion() -> None:
    right = grade(ExerciseKind.SINGLE_CHOICE, SINGLE, {"choice": "b"})
    bad = grade(ExerciseKind.SINGLE_CHOICE, SINGLE, {"choice": "a"})
    assert (right.score, bad.score) == (100, 0)
    assert bad.items[0].feedback == "Porque B."


@pytest.mark.ac("AC-003-7")
def test_branching_suma_ponderada() -> None:
    half = grade(ExerciseKind.BRANCHING, BRANCHING, {"choices": {"s1": "meh", "s2": "ok"}})
    assert half.score == 75  # (5 + 10) / 20
    assert [i.correct for i in half.items] == [False, True]
    assert half.items[0].feedback == "Regular"
    assert grade(ExerciseKind.BRANCHING, BRANCHING, {"choices": {"s1": "ok"}}).score == 50


@pytest.mark.ac("AC-003-8")
@pytest.mark.parametrize(
    ("kind", "answer"),
    [
        (ExerciseKind.ORDERING, {"order": "no-es-lista"}),
        (ExerciseKind.ORDERING, {"order": [1, 2]}),
        (ExerciseKind.MATCHING, {"assignments": ["x"]}),
        (ExerciseKind.MATCHING, {"assignments": {"l1": 3}}),
        (ExerciseKind.SINGLE_CHOICE, {"choice": 7}),
        (ExerciseKind.QUIZ, {}),
        (ExerciseKind.BRANCHING, {"choices": None}),
        (ExerciseKind.BRANCHING, "texto"),
    ],
)
def test_respuestas_con_forma_invalida_se_rechazan(kind: ExerciseKind, answer: object) -> None:
    with pytest.raises(InvalidAnswer):
        grade(kind, SPECS[kind], answer)


def _flatten_keys(value: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for k, v in value.items():
            keys.add(k)
            keys |= _flatten_keys(v)
    elif isinstance(value, list):
        for item in value:
            keys |= _flatten_keys(item)
    return keys


@pytest.mark.ac("AC-003-6")
@pytest.mark.parametrize("kind", list(SPECS))
def test_la_version_publica_no_filtra_soluciones(kind: ExerciseKind) -> None:
    public = to_public(kind, SPECS[kind], seed="semilla")
    leaked = _flatten_keys(public) & {"correct", "correct_order", "pairs", "points", "feedback",
                                      "explanation"}  # fmt: skip
    assert not leaked, f"claves de solucion expuestas: {leaked}"
    assert public["prompt"]


@pytest.mark.ac("AC-003-6")
def test_ordering_publico_esta_barajado_de_forma_determinista() -> None:
    first = to_public(ExerciseKind.ORDERING, ORDERING, seed="m1")
    again = to_public(ExerciseKind.ORDERING, ORDERING, seed="m1")
    assert first == again
    ids = [i["id"] for i in first["items"]]
    assert sorted(ids) == sorted(ORDERING["correct_order"])
    assert ids != ORDERING["correct_order"], "no debe salir ya resuelto"


@pytest.mark.ac("AC-003-15")
@pytest.mark.parametrize(
    ("kind", "broken"),
    [
        (ExerciseKind.ORDERING, {**ORDERING, "correct_order": ["x", "y"]}),
        (ExerciseKind.ORDERING, {**ORDERING, "prompt": ""}),
        (ExerciseKind.MATCHING, {**MATCHING, "pairs": {"l1": "r9", "l2": "r1", "l3": "r1", "l4": "r1"}}),
        (ExerciseKind.MATCHING, {**MATCHING, "pairs": {"l1": "r1"}}),
        (ExerciseKind.SINGLE_CHOICE, {**SINGLE, "correct": "zzz"}),
        (ExerciseKind.QUIZ, {"prompt": "x", "questions": []}),
        (ExerciseKind.BRANCHING, {"prompt": "x", "steps": [
            {"id": "s", "situation": "x", "options": [
                {"id": "a", "label": "A", "points": 0}, {"id": "b", "label": "B", "points": 0}]}]}),
    ],
)  # fmt: skip
def test_validate_spec_rechaza_contenido_roto(kind: ExerciseKind, broken: dict) -> None:
    with pytest.raises(InvalidExerciseSpec):
        validate_spec(kind, broken)
