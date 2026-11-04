"""Validacion, version publica y correccion de ejercicios. Funciones puras.

Formas de `spec` (privada, con solucion) y de `answer` por tipo:

- ordering:      spec {prompt, items[{id,label}], correct_order[id]}      answer {order[id]}
- matching:      spec {prompt, left[{id,label}], right[{id,label}], pairs{leftId: rightId}}
                 answer {assignments{leftId: rightId}}
- single_choice: spec {prompt, options[{id,label}], correct, explanation}   answer {choice}
- quiz:          spec {prompt?, questions[{id,prompt,options,correct,explanation}]}
                 answer {answers{questionId: optionId}}
- branching:     spec {prompt, steps[{id,situation,options[{id,label,points,feedback}]}]}
                 answer {choices{stepId: optionId}}
"""

import random
from dataclasses import dataclass
from typing import Any

from unsa_audit.learning.domain.route import ExerciseKind

Spec = dict[str, Any]


class InvalidExerciseSpec(ValueError):
    """La especificacion del ejercicio (contenido) esta mal formada."""


class InvalidAnswer(ValueError):
    """La respuesta enviada no tiene la forma esperada."""


@dataclass(frozen=True)
class ItemFeedback:
    id: str
    correct: bool
    feedback: str = ""


@dataclass(frozen=True)
class GradeResult:
    score: int  # 0..100
    items: tuple[ItemFeedback, ...]


# ----------------------------------------------------------------------------- utilidades


def _pct(correct: int, total: int) -> int:
    return (100 * correct + total // 2) // total if total else 0


def _need(cond: bool, message: str) -> None:
    if not cond:
        raise InvalidExerciseSpec(message)


def _labelled_ids(items: Any, what: str) -> list[str]:
    _need(isinstance(items, list) and len(items) > 0, f"{what} debe ser una lista no vacia")
    ids: list[str] = []
    for item in items:
        ok = isinstance(item, dict) and isinstance(item.get("id"), str) and bool(item.get("label"))
        _need(ok, f"{what}: cada elemento necesita id y label")
        ids.append(item["id"])
    _need(len(set(ids)) == len(ids), f"{what}: ids repetidos")
    return ids


def _shuffled(items: list[Any], seed: str, avoid_order: list[Any] | None = None) -> list[Any]:
    result = list(items)
    random.Random(seed).shuffle(result)
    if avoid_order is not None and len(result) > 1 and result == avoid_order:
        result = result[1:] + result[:1]
    return result


def _expect_dict(answer: Any, key: str) -> dict[str, str]:
    value = answer.get(key) if isinstance(answer, dict) else None
    if not isinstance(value, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in value.items()
    ):
        raise InvalidAnswer(f"`{key}` debe ser un objeto de textos")
    return value


# ----------------------------------------------------------------------------- validacion


def _validate_options(options: Any, correct: Any, what: str) -> None:
    ids = _labelled_ids(options, f"{what}.options")
    _need(len(ids) >= 2, f"{what}: se necesitan al menos 2 opciones")
    _need(correct in ids, f"{what}: `correct` no es una opcion")


def validate_spec(kind: ExerciseKind, spec: Spec) -> None:
    _need(isinstance(spec, dict) and bool(spec.get("prompt") or kind is ExerciseKind.QUIZ),
          "falta `prompt`")  # fmt: skip
    if kind is ExerciseKind.ORDERING:
        ids = _labelled_ids(spec.get("items"), "items")
        order = spec.get("correct_order")
        _need(isinstance(order, list) and sorted(order) == sorted(ids),
              "`correct_order` debe ser una permutacion de los ids")  # fmt: skip
    elif kind is ExerciseKind.MATCHING:
        left = _labelled_ids(spec.get("left"), "left")
        right = _labelled_ids(spec.get("right"), "right")
        pairs: Any = spec.get("pairs")
        _need(isinstance(pairs, dict) and set(pairs) == set(left),
              "`pairs` debe cubrir todos los elementos de `left`")  # fmt: skip
        _need(all(v in right for v in dict(pairs).values()), "`pairs` apunta a un id inexistente")
    elif kind is ExerciseKind.SINGLE_CHOICE:
        _validate_options(spec.get("options"), spec.get("correct"), "single_choice")
    elif kind is ExerciseKind.QUIZ:
        questions: Any = spec.get("questions")
        _need(isinstance(questions, list) and len(questions) > 0, "`questions` vacio")
        ids = [q.get("id") for q in list(questions)]
        _need(all(isinstance(i, str) for i in ids) and len(set(ids)) == len(ids),
              "ids de pregunta invalidos o repetidos")  # fmt: skip
        for q in list(questions):
            _need(bool(q.get("prompt")), f"pregunta {q['id']} sin `prompt`")
            _validate_options(q.get("options"), q.get("correct"), f"pregunta {q['id']}")
    elif kind is ExerciseKind.BRANCHING:
        steps: Any = spec.get("steps")
        _need(isinstance(steps, list) and len(steps) > 0, "`steps` vacio")
        ids = [s.get("id") for s in list(steps)]
        _need(all(isinstance(i, str) for i in ids) and len(set(ids)) == len(ids),
              "ids de paso invalidos o repetidos")  # fmt: skip
        for step in list(steps):
            _need(bool(step.get("situation")), f"paso {step['id']} sin `situation`")
            _labelled_ids(step.get("options"), f"paso {step['id']}.options")
            points = [o.get("points") for o in step["options"]]
            _need(all(isinstance(p, int) and 0 <= p <= 10 for p in points),
                  f"paso {step['id']}: `points` debe ser entero 0..10")  # fmt: skip
            _need(max(points) > 0, f"paso {step['id']}: ninguna opcion suma puntos")
    elif kind is ExerciseKind.SOA_FORM:
        _need(bool(spec.get("scenario")), "falta `scenario`")
        reasons = _labelled_ids(spec.get("reasons"), "reasons")
        controls: Any = spec.get("controls")
        _need(isinstance(controls, list) and len(controls) > 0, "`controls` vacio")
        ids = _labelled_ids(controls, "controls")
        for control in list(controls):
            _need(
                isinstance(control.get("applies"), bool),
                f"{control['id']}: `applies` debe ser bool",
            )
            _need(control.get("reason") in reasons, f"{control['id']}: `reason` no es una opcion")
            _need(bool(control.get("explanation")), f"{control['id']}: falta `explanation`")
        _need(len(ids) == len(set(ids)), "controles repetidos")


# ----------------------------------------------------------------------------- version publica


def _strip(options: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [{"id": o["id"], "label": o["label"]} for o in options]


def to_public(kind: ExerciseKind, spec: Spec, seed: str) -> Spec:
    """Version del ejercicio apta para el cliente: sin respuestas, puntos ni explicaciones."""
    prompt = spec.get("prompt", "")
    if kind is ExerciseKind.ORDERING:
        items = _strip(spec["items"])
        by_id = {i["id"]: i for i in items}
        correct = [by_id[i] for i in spec["correct_order"]]
        return {"prompt": prompt, "items": _shuffled(items, seed, avoid_order=correct)}
    if kind is ExerciseKind.MATCHING:
        return {
            "prompt": prompt,
            "left": _shuffled(_strip(spec["left"]), seed),
            "right": _strip(spec["right"]),
        }
    if kind is ExerciseKind.SOA_FORM:
        return {
            "prompt": prompt,
            "scenario": spec["scenario"],
            "reasons": _strip(spec["reasons"]),
            "controls": _strip(spec["controls"]),
        }
    if kind is ExerciseKind.SINGLE_CHOICE:
        return {"prompt": prompt, "options": _strip(spec["options"])}
    if kind is ExerciseKind.QUIZ:
        return {
            "prompt": prompt,
            "questions": [
                {"id": q["id"], "prompt": q["prompt"], "options": _strip(q["options"])}
                for q in spec["questions"]
            ],
        }
    return {  # BRANCHING
        "prompt": prompt,
        "steps": [
            {"id": s["id"], "situation": s["situation"], "options": _strip(s["options"])}
            for s in spec["steps"]
        ],
    }


# ----------------------------------------------------------------------------- correccion


def _grade_ordering(spec: Spec, answer: Any) -> GradeResult:
    order = answer.get("order") if isinstance(answer, dict) else None
    if not isinstance(order, list) or not all(isinstance(i, str) for i in order):
        raise InvalidAnswer("`order` debe ser una lista de ids")
    correct_order: list[str] = spec["correct_order"]
    labels = {i["id"]: i["label"] for i in spec["items"]}
    items = tuple(
        ItemFeedback(id=item_id, correct=index < len(order) and order[index] == item_id,
                     feedback=labels[item_id])
        for index, item_id in enumerate(correct_order)
    )  # fmt: skip
    return GradeResult(_pct(sum(i.correct for i in items), len(items)), items)


def _grade_matching(spec: Spec, answer: Any) -> GradeResult:
    assignments = _expect_dict(answer, "assignments")
    labels = {i["id"]: i["label"] for i in spec["left"]}
    items = tuple(
        ItemFeedback(id=left_id, correct=assignments.get(left_id) == right_id,
                     feedback=labels[left_id])
        for left_id, right_id in spec["pairs"].items()
    )  # fmt: skip
    return GradeResult(_pct(sum(i.correct for i in items), len(items)), items)


def _grade_single_choice(spec: Spec, answer: Any) -> GradeResult:
    choice = answer.get("choice") if isinstance(answer, dict) else None
    if not isinstance(choice, str):
        raise InvalidAnswer("`choice` debe ser un id")
    ok = choice == spec["correct"]
    return GradeResult(100 if ok else 0, (ItemFeedback("choice", ok, spec.get("explanation", "")),))


def _grade_quiz(spec: Spec, answer: Any) -> GradeResult:
    answers = _expect_dict(answer, "answers")
    items = tuple(
        ItemFeedback(
            id=q["id"],
            correct=answers.get(q["id"]) == q["correct"],
            feedback=q.get("explanation", ""),
        )
        for q in spec["questions"]
    )
    return GradeResult(_pct(sum(i.correct for i in items), len(items)), items)


def _grade_branching(spec: Spec, answer: Any) -> GradeResult:
    choices = _expect_dict(answer, "choices")
    earned = best = 0
    items: list[ItemFeedback] = []
    for step in spec["steps"]:
        top = max(o["points"] for o in step["options"])
        chosen = next((o for o in step["options"] if o["id"] == choices.get(step["id"])), None)
        points = chosen["points"] if chosen else 0
        earned, best = earned + points, best + top
        items.append(
            ItemFeedback(step["id"], points == top, chosen.get("feedback", "") if chosen else "")
        )
    return GradeResult(_pct(earned, best), tuple(items))


def _grade_soa_form(spec: Spec, answer: Any) -> GradeResult:
    decisions = answer.get("decisions") if isinstance(answer, dict) else None
    if not isinstance(decisions, dict):
        raise InvalidAnswer("`decisions` debe ser un objeto")
    for decision in decisions.values():
        if (
            not isinstance(decision, dict)
            or not isinstance(decision.get("applies"), bool)
            or not isinstance(decision.get("reason"), str)
        ):
            raise InvalidAnswer("cada decision necesita `applies` (bool) y `reason` (texto)")

    items: list[ItemFeedback] = []
    points = 0
    for control in spec["controls"]:
        decision = decisions.get(control["id"], {})
        applies_ok = decision.get("applies") is control["applies"]
        reason_ok = decision.get("reason") == control["reason"]
        points += int(applies_ok) + int(reason_ok)
        items.append(ItemFeedback(control["id"], applies_ok and reason_ok, control["explanation"]))
    return GradeResult(_pct(points, 2 * len(items)), tuple(items))


_GRADERS = {
    ExerciseKind.SOA_FORM: _grade_soa_form,
    ExerciseKind.ORDERING: _grade_ordering,
    ExerciseKind.MATCHING: _grade_matching,
    ExerciseKind.SINGLE_CHOICE: _grade_single_choice,
    ExerciseKind.QUIZ: _grade_quiz,
    ExerciseKind.BRANCHING: _grade_branching,
}


def grade(kind: ExerciseKind, spec: Spec, answer: Any) -> GradeResult:
    return _GRADERS[kind](spec, answer)
