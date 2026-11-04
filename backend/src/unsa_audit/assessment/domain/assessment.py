"""Evaluacion para roles controller/processor: preguntas, correccion y resultados (puro)."""

import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class Profile(StrEnum):
    CONTROLLER = "controller"
    PROCESSOR = "processor"


class AttemptStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"


class InvalidAnswers(ValueError):
    """Las respuestas enviadas no tienen la forma esperada."""


@dataclass(frozen=True)
class Option:
    id: str
    label: str


@dataclass(frozen=True)
class Question:
    id: str
    competency: str
    requirement_code: str
    prompt: str
    options: tuple[Option, ...]
    correct: str
    explanation: str


@dataclass(frozen=True)
class AssessmentDefinition:
    profile: Profile
    title: str
    pass_score: int
    competencies: dict[str, str]
    questions: tuple[Question, ...]


@dataclass(frozen=True)
class ItemResult:
    question_id: str
    prompt: str
    correct: bool
    chosen_label: str | None
    correct_label: str
    explanation: str
    competency: str
    requirement_code: str


@dataclass(frozen=True)
class ScoreGroup:
    key: str
    label: str
    correct: int
    total: int

    @property
    def percent(self) -> int:
        return pct(self.correct, self.total)


@dataclass(frozen=True)
class AssessmentResult:
    score: int
    passed: bool
    pass_score: int
    competencies: list[ScoreGroup]
    requirements: list[ScoreGroup]
    items: list[ItemResult] = field(default_factory=list)


@dataclass(frozen=True)
class Attempt:
    id: UUID
    user_id: UUID
    profile: Profile
    question_ids: list[str]
    status: AttemptStatus
    started_at: datetime
    answers: dict[str, str] | None = None
    result: AssessmentResult | None = None
    finished_at: datetime | None = None


def pct(correct: int, total: int) -> int:
    return (100 * correct + total // 2) // total if total else 0


def ordered_question_ids(definition: AssessmentDefinition, seed: str) -> list[str]:
    """Orden determinista de las preguntas para un intento (semilla = id del intento)."""
    ids = [q.id for q in definition.questions]
    random.Random(seed).shuffle(ids)
    return ids


def validate_answers(answers: Any) -> dict[str, str]:
    if not isinstance(answers, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in answers.items()
    ):
        raise InvalidAnswers("`answers` debe ser un objeto {pregunta: opcion}")
    return answers


def grade(
    definition: AssessmentDefinition,
    question_ids: list[str],
    answers: dict[str, str],
    requirement_labels: dict[str, str],
) -> AssessmentResult:
    """Corrige las preguntas del intento. Sin responder o id desconocido = incorrecta."""
    by_id = {q.id: q for q in definition.questions}
    questions = [by_id[qid] for qid in question_ids if qid in by_id]

    items: list[ItemResult] = []
    for q in questions:
        options = {o.id: o.label for o in q.options}
        chosen = answers.get(q.id)
        items.append(
            ItemResult(
                question_id=q.id,
                prompt=q.prompt,
                correct=chosen == q.correct,
                chosen_label=options.get(chosen) if chosen else None,
                correct_label=options[q.correct],
                explanation=q.explanation,
                competency=q.competency,
                requirement_code=q.requirement_code,
            )
        )

    def group(key_of: Any, label_of: Any) -> list[ScoreGroup]:
        order: dict[str, list[ItemResult]] = {}
        for item in items:
            order.setdefault(key_of(item), []).append(item)
        return [
            ScoreGroup(key, label_of(key), sum(i.correct for i in group_items), len(group_items))
            for key, group_items in order.items()
        ]

    correct = sum(i.correct for i in items)
    score = pct(correct, len(items))
    return AssessmentResult(
        score=score,
        passed=score >= definition.pass_score,
        pass_score=definition.pass_score,
        competencies=group(lambda i: i.competency, lambda k: definition.competencies.get(k, k)),
        requirements=group(lambda i: i.requirement_code, lambda k: requirement_labels.get(k, k)),
        items=items,
    )
