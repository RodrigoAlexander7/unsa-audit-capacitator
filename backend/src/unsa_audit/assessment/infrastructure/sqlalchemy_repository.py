from dataclasses import asdict
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from unsa_audit.assessment.domain.assessment import (
    AssessmentResult,
    Attempt,
    AttemptStatus,
    ItemResult,
    Profile,
    ScoreGroup,
)
from unsa_audit.assessment.infrastructure.models import AssessmentModel


def result_to_dict(result: AssessmentResult) -> dict[str, Any]:
    return {
        "score": result.score,
        "passed": result.passed,
        "pass_score": result.pass_score,
        "competencies": [asdict(g) for g in result.competencies],
        "requirements": [asdict(g) for g in result.requirements],
        "items": [asdict(i) for i in result.items],
    }


def result_from_dict(data: dict[str, Any]) -> AssessmentResult:
    return AssessmentResult(
        score=data["score"],
        passed=data["passed"],
        pass_score=data["pass_score"],
        competencies=[ScoreGroup(**g) for g in data["competencies"]],
        requirements=[ScoreGroup(**g) for g in data["requirements"]],
        items=[ItemResult(**i) for i in data["items"]],
    )


def _attempt(m: AssessmentModel) -> Attempt:
    return Attempt(
        id=m.id,
        user_id=m.user_id,
        profile=Profile(m.profile),
        question_ids=list(m.question_ids),
        status=AttemptStatus(m.status),
        started_at=m.started_at,
        answers=m.answers,
        result=result_from_dict(m.result) if m.result else None,
        finished_at=m.finished_at,
    )


class SqlAlchemyAssessmentRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    async def add(self, attempt: Attempt) -> None:
        async with self._sf() as session, session.begin():
            session.add(
                AssessmentModel(
                    id=attempt.id,
                    user_id=attempt.user_id,
                    profile=attempt.profile.value,
                    question_ids=attempt.question_ids,
                    status=attempt.status.value,
                    started_at=attempt.started_at,
                )
            )

    async def get(self, attempt_id: UUID) -> Attempt | None:
        async with self._sf() as session:
            row = await session.get(AssessmentModel, attempt_id)
            return _attempt(row) if row else None

    async def save(self, attempt: Attempt) -> bool:
        assert attempt.result is not None
        async with self._sf() as session, session.begin():
            row = await session.get(AssessmentModel, attempt.id, with_for_update=True)
            if row is None or row.status != AttemptStatus.IN_PROGRESS.value:
                return False
            row.status = attempt.status.value
            row.answers = attempt.answers
            row.score = attempt.result.score
            row.passed = attempt.result.passed
            row.result = result_to_dict(attempt.result)
            row.finished_at = attempt.finished_at
            return True

    async def list_for_user(self, user_id: UUID) -> list[Attempt]:
        async with self._sf() as session:
            rows = await session.scalars(
                select(AssessmentModel)
                .where(AssessmentModel.user_id == user_id)
                .order_by(AssessmentModel.started_at.desc())
            )
            return [_attempt(r) for r in rows]
