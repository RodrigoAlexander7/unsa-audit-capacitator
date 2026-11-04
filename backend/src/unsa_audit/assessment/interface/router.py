from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from unsa_audit.assessment.application.errors import (
    AlreadySubmitted,
    AttemptNotFound,
    UnknownProfile,
)
from unsa_audit.assessment.application.use_cases import AttemptView
from unsa_audit.assessment.domain.assessment import (
    AssessmentResult,
    Attempt,
    AttemptStatus,
    InvalidAnswers,
    Profile,
)
from unsa_audit.identity.interface.dependencies import CurrentUser

router = APIRouter(prefix="/assessments", tags=["assessment"])


class StartRequest(BaseModel):
    profile: Profile


class SubmitRequest(BaseModel):
    answers: dict[str, Any]


class OptionResponse(BaseModel):
    id: str
    label: str


class QuestionResponse(BaseModel):
    id: str
    prompt: str
    options: list[OptionResponse]


class GroupResponse(BaseModel):
    key: str
    label: str
    correct: int
    total: int
    percent: int


class ItemResponse(BaseModel):
    question_id: str
    prompt: str
    correct: bool
    chosen_label: str | None
    correct_label: str
    explanation: str
    competency: str
    requirement_code: str


class ResultResponse(BaseModel):
    score: int
    passed: bool
    pass_score: int
    competencies: list[GroupResponse]
    requirements: list[GroupResponse]
    items: list[ItemResponse]

    @classmethod
    def from_domain(cls, r: AssessmentResult) -> "ResultResponse":
        def groups(items):  # type: ignore[no-untyped-def]
            return [
                GroupResponse(
                    key=g.key, label=g.label, correct=g.correct, total=g.total, percent=g.percent
                )
                for g in items
            ]

        return cls(
            score=r.score,
            passed=r.passed,
            pass_score=r.pass_score,
            competencies=groups(r.competencies),
            requirements=groups(r.requirements),
            items=[ItemResponse(**vars(i)) for i in r.items],
        )


class AttemptSummaryResponse(BaseModel):
    id: str
    profile: str
    status: str
    score: int | None
    passed: bool | None
    started_at: datetime
    finished_at: datetime | None

    @classmethod
    def from_domain(cls, a: Attempt) -> "AttemptSummaryResponse":
        return cls(
            id=str(a.id),
            profile=a.profile.value,
            status=a.status.value,
            score=a.result.score if a.result else None,
            passed=a.result.passed if a.result else None,
            started_at=a.started_at,
            finished_at=a.finished_at,
        )


class AttemptResponse(AttemptSummaryResponse):
    title: str
    pass_score: int
    questions: list[QuestionResponse]
    result: ResultResponse | None

    @classmethod
    def from_view(cls, view: AttemptView) -> "AttemptResponse":
        a, d = view.attempt, view.definition
        by_id = {q.id: q for q in d.questions}
        questions = [
            QuestionResponse(
                id=q.id,
                prompt=q.prompt,
                options=[OptionResponse(id=o.id, label=o.label) for o in q.options],
            )
            for q in (by_id[qid] for qid in a.question_ids if qid in by_id)
        ]
        base = AttemptSummaryResponse.from_domain(a)
        return cls(
            **base.model_dump(),
            title=d.title,
            pass_score=d.pass_score,
            # Una vez enviada, las preguntas ya no hacen falta (el resultado las incluye).
            questions=questions if a.status is AttemptStatus.IN_PROGRESS else [],
            result=ResultResponse.from_domain(a.result) if a.result else None,
        )


def _not_found() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "Evaluación no encontrada")


@router.post("", response_model=AttemptResponse, status_code=status.HTTP_201_CREATED)
async def start(body: StartRequest, user: CurrentUser, request: Request) -> AttemptResponse:
    try:
        view = await request.app.state.start_assessment.execute(user.id, body.profile)
    except UnknownProfile as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Perfil sin banco") from exc
    return AttemptResponse.from_view(view)


@router.get("", response_model=list[AttemptSummaryResponse])
async def list_mine(user: CurrentUser, request: Request) -> list[AttemptSummaryResponse]:
    attempts = await request.app.state.list_assessments.execute(user.id)
    return [AttemptSummaryResponse.from_domain(a) for a in attempts]


@router.get("/{assessment_id}", response_model=AttemptResponse)
async def get_one(assessment_id: UUID, user: CurrentUser, request: Request) -> AttemptResponse:
    try:
        view = await request.app.state.get_assessment.execute(user.id, assessment_id)
    except AttemptNotFound as exc:
        raise _not_found() from exc
    return AttemptResponse.from_view(view)


@router.post("/{assessment_id}/submit", response_model=AttemptResponse)
async def submit(
    assessment_id: UUID, body: SubmitRequest, user: CurrentUser, request: Request
) -> AttemptResponse:
    try:
        view = await request.app.state.submit_assessment.execute(
            user.id, assessment_id, body.answers
        )
    except AttemptNotFound as exc:
        raise _not_found() from exc
    except AlreadySubmitted as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Esta evaluación ya fue enviada. Inicia una nueva."
        ) from exc
    except InvalidAnswers as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
    return AttemptResponse.from_view(view)
