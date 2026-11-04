"""Lee `content/assessment/<perfil>.json` y valida el banco de preguntas."""

import json
from pathlib import Path
from typing import Any

from unsa_audit.assessment.domain.assessment import AssessmentDefinition, Option, Profile, Question
from unsa_audit.documents.application.pims_use_cases import ListPimsRequirements


class QuestionBankError(ValueError):
    """El banco de preguntas esta mal formado."""


def _question(raw: dict[str, Any], competencies: dict[str, str], path: Path) -> Question:
    try:
        options = tuple(Option(o["id"], o["label"]) for o in raw["options"])
        question = Question(
            id=raw["id"],
            competency=raw["competency"],
            requirement_code=raw["requirement"],
            prompt=raw["prompt"],
            options=options,
            correct=raw["correct"],
            explanation=raw["explanation"],
        )
    except (KeyError, TypeError) as exc:
        raise QuestionBankError(f"{path}: pregunta mal formada ({exc})") from exc
    ids = [o.id for o in options]
    if len(ids) < 2 or len(set(ids)) != len(ids) or question.correct not in ids:
        raise QuestionBankError(f"{path}: {question.id}: opciones invalidas")
    if question.competency not in competencies:
        raise QuestionBankError(f"{path}: {question.id}: competencia desconocida")
    return question


def load_definition(path: Path) -> AssessmentDefinition:
    raw = json.loads(path.read_text(encoding="utf-8"))
    try:
        profile = Profile(raw["profile"])
        competencies = dict(raw["competencies"])
        questions = tuple(_question(q, competencies, path) for q in raw["questions"])
        definition = AssessmentDefinition(
            profile=profile,
            title=raw["title"],
            pass_score=int(raw.get("pass_score", 70)),
            competencies=competencies,
            questions=questions,
        )
    except (KeyError, ValueError) as exc:
        raise QuestionBankError(f"{path}: {exc}") from exc
    if not questions or len({q.id for q in questions}) != len(questions):
        raise QuestionBankError(f"{path}: preguntas vacias o con ids repetidos")
    return definition


class FileQuestionBank:
    def __init__(self, content_dir: Path) -> None:
        self._dir = content_dir / "assessment"
        self._cache: dict[Profile, AssessmentDefinition] | None = None

    def _load(self) -> dict[Profile, AssessmentDefinition]:
        if self._cache is None:
            definitions = [load_definition(p) for p in sorted(self._dir.glob("*.json"))]
            self._cache = {d.profile: d for d in definitions}
        return self._cache

    def get(self, profile: Profile) -> AssessmentDefinition | None:
        return self._load().get(profile)


class PimsRequirementCatalog:
    """Etiquetas '<clausula> <titulo>' de los requisitos del PIMS (via el modulo documents)."""

    def __init__(self, list_requirements: ListPimsRequirements) -> None:
        self._list = list_requirements

    async def labels(self) -> dict[str, str]:
        return {
            v.requirement.code: f"{v.requirement.clause_ref} {v.requirement.title}"
            for v in await self._list.execute()
        }
