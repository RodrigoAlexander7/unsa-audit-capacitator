from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from unsa_audit.assessment.application.errors import (
    AlreadySubmitted,
    AttemptNotFound,
    UnknownProfile,
)
from unsa_audit.assessment.application.ports import (
    AssessmentRepository,
    QuestionBank,
    RequirementCatalog,
)
from unsa_audit.assessment.domain.assessment import (
    AssessmentDefinition,
    Attempt,
    AttemptStatus,
    Profile,
    grade,
    ordered_question_ids,
    validate_answers,
)

Clock = Callable[[], datetime]


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class AttemptView:
    attempt: Attempt
    definition: AssessmentDefinition


def _definition(bank: QuestionBank, profile: Profile) -> AssessmentDefinition:
    definition = bank.get(profile)
    if definition is None:
        raise UnknownProfile
    return definition


class StartAssessment:
    def __init__(
        self,
        bank: QuestionBank,
        repo: AssessmentRepository,
        clock: Clock = _utcnow,
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._bank = bank
        self._repo = repo
        self._clock = clock
        self._id_factory = id_factory

    async def execute(self, user_id: UUID, profile: Profile) -> AttemptView:
        definition = _definition(self._bank, profile)
        attempt_id = self._id_factory()
        attempt = Attempt(
            id=attempt_id,
            user_id=user_id,
            profile=profile,
            question_ids=ordered_question_ids(definition, str(attempt_id)),
            status=AttemptStatus.IN_PROGRESS,
            started_at=self._clock(),
        )
        await self._repo.add(attempt)
        return AttemptView(attempt, definition)


async def _own_attempt(repo: AssessmentRepository, user_id: UUID, attempt_id: UUID) -> Attempt:
    attempt = await repo.get(attempt_id)
    if attempt is None or attempt.user_id != user_id:
        raise AttemptNotFound
    return attempt


class GetAssessment:
    def __init__(self, bank: QuestionBank, repo: AssessmentRepository) -> None:
        self._bank = bank
        self._repo = repo

    async def execute(self, user_id: UUID, attempt_id: UUID) -> AttemptView:
        attempt = await _own_attempt(self._repo, user_id, attempt_id)
        return AttemptView(attempt, _definition(self._bank, attempt.profile))


class SubmitAssessment:
    def __init__(
        self,
        bank: QuestionBank,
        repo: AssessmentRepository,
        catalog: RequirementCatalog,
        clock: Clock = _utcnow,
    ) -> None:
        self._bank = bank
        self._repo = repo
        self._catalog = catalog
        self._clock = clock

    async def execute(self, user_id: UUID, attempt_id: UUID, answers: Any) -> AttemptView:
        attempt = await _own_attempt(self._repo, user_id, attempt_id)
        if attempt.status is AttemptStatus.FINISHED:
            raise AlreadySubmitted
        clean = validate_answers(answers)  # InvalidAnswers
        definition = _definition(self._bank, attempt.profile)
        result = grade(definition, attempt.question_ids, clean, await self._catalog.labels())
        finished = replace(
            attempt,
            status=AttemptStatus.FINISHED,
            answers=clean,
            result=result,
            finished_at=self._clock(),
        )
        if not await self._repo.save(finished):  # otra peticion se adelanto
            raise AlreadySubmitted
        return AttemptView(finished, definition)


class ListAssessments:
    def __init__(self, repo: AssessmentRepository) -> None:
        self._repo = repo

    async def execute(self, user_id: UUID) -> list[Attempt]:
        return await self._repo.list_for_user(user_id)
