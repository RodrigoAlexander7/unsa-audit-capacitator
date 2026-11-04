"""Resuelve ejercicios a partir de su spec privada (solo para tests)."""

from typing import Any

from unsa_audit.learning.domain.route import ExerciseKind


def solve(kind: ExerciseKind, spec: dict[str, Any]) -> dict[str, Any]:
    """Respuesta perfecta (100 puntos) para el ejercicio."""
    if kind is ExerciseKind.ORDERING:
        return {"order": list(spec["correct_order"])}
    if kind is ExerciseKind.MATCHING:
        return {"assignments": dict(spec["pairs"])}
    if kind is ExerciseKind.SINGLE_CHOICE:
        return {"choice": spec["correct"]}
    if kind is ExerciseKind.QUIZ:
        return {"answers": {q["id"]: q["correct"] for q in spec["questions"]}}
    return {
        "choices": {
            step["id"]: max(step["options"], key=lambda o: o["points"])["id"]
            for step in spec["steps"]
        }
    }


def wrong(kind: ExerciseKind) -> dict[str, Any]:
    """Respuesta vacia de forma valida: puntaje 0 (o minimo)."""
    return {
        ExerciseKind.ORDERING: {"order": []},
        ExerciseKind.MATCHING: {"assignments": {}},
        ExerciseKind.SINGLE_CHOICE: {"choice": "no-existe"},
        ExerciseKind.QUIZ: {"answers": {}},
        ExerciseKind.BRANCHING: {"choices": {}},
    }[kind]
