from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from unsa_audit.analytics.application.errors import (
    AdvisorUnavailable,
    InvalidQuestion,
    RouteStatsNotFound,
)
from unsa_audit.analytics.application.use_cases import MAX_QUESTION_CHARS
from unsa_audit.analytics.domain.stats import (
    AdvisorQuery,
    AssessmentProfileStats,
    GroupAverage,
    ModuleStats,
    RouteStats,
)
from unsa_audit.identity.interface.dependencies import SuperAdmin

router = APIRouter(prefix="/admin", tags=["analytics"])


class RouteStatsResponse(BaseModel):
    code: str
    order: int
    title: str
    hours: int
    modules_total: int
    enrolled: int
    in_progress: int
    completed: int
    completion_rate: int
    avg_progress: int
    avg_hours_credited: float
    attempts: int
    pass_rate: int
    stalled: int

    @classmethod
    def from_domain(cls, r: RouteStats) -> "RouteStatsResponse":
        return cls(**vars(r))


class ModuleStatsResponse(BaseModel):
    id: str
    order: int
    title: str
    minutes: int
    is_final: bool
    attempts: int
    learners_attempted: int
    learners_completed: int
    avg_score: int | None
    pass_rate: int | None
    hardest: bool

    @classmethod
    def from_domain(cls, m: ModuleStats) -> "ModuleStatsResponse":
        return cls(
            id=str(m.id),
            order=m.order,
            title=m.title,
            minutes=m.minutes,
            is_final=m.is_final,
            attempts=m.attempts,
            learners_attempted=m.learners_attempted,
            learners_completed=m.learners_completed,
            avg_score=m.avg_score,
            pass_rate=m.pass_rate,
            hardest=m.hardest,
        )


class RouteDetailStatsResponse(BaseModel):
    route: RouteStatsResponse
    modules: list[ModuleStatsResponse]


class GroupAverageResponse(BaseModel):
    key: str
    label: str
    average: int
    samples: int

    @classmethod
    def from_domain(cls, g: GroupAverage) -> "GroupAverageResponse":
        return cls(key=g.key, label=g.label, average=g.average, samples=g.samples)


class AssessmentProfileStatsResponse(BaseModel):
    profile: str
    finished: int
    avg_score: int
    pass_rate: int
    competencies: list[GroupAverageResponse]
    requirements: list[GroupAverageResponse]

    @classmethod
    def from_domain(cls, a: AssessmentProfileStats) -> "AssessmentProfileStatsResponse":
        return cls(
            profile=a.profile,
            finished=a.finished,
            avg_score=a.avg_score,
            pass_rate=a.pass_rate,
            competencies=[GroupAverageResponse.from_domain(g) for g in a.competencies],
            requirements=[GroupAverageResponse.from_domain(g) for g in a.requirements],
        )


class SnapshotResponse(BaseModel):
    hash: str
    data: dict[str, Any]


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=MAX_QUESTION_CHARS)


class AdvisorQueryResponse(BaseModel):
    id: str
    question: str
    status: str
    answer: str | None
    error: str | None
    duration_ms: int
    snapshot_hash: str
    created_at: datetime

    @classmethod
    def from_domain(cls, q: AdvisorQuery) -> "AdvisorQueryResponse":
        return cls(
            id=str(q.id),
            question=q.question,
            status=q.status,
            answer=q.answer,
            error=q.error,
            duration_ms=q.duration_ms,
            snapshot_hash=q.snapshot_hash,
            created_at=q.created_at,
        )


@router.get("/stats/routes", response_model=list[RouteStatsResponse])
async def route_stats(_: SuperAdmin, request: Request) -> list[RouteStatsResponse]:
    stats = await request.app.state.get_route_stats.execute()
    return [RouteStatsResponse.from_domain(r) for r in stats]


@router.get("/stats/routes/{code}", response_model=RouteDetailStatsResponse)
async def route_detail_stats(
    code: str, _: SuperAdmin, request: Request
) -> RouteDetailStatsResponse:
    try:
        detail = await request.app.state.get_route_detail_stats.execute(code)
    except RouteStatsNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ruta no encontrada") from exc
    return RouteDetailStatsResponse(
        route=RouteStatsResponse.from_domain(detail.route),
        modules=[ModuleStatsResponse.from_domain(m) for m in detail.modules],
    )


@router.get("/stats/assessments", response_model=list[AssessmentProfileStatsResponse])
async def assessment_stats(_: SuperAdmin, request: Request) -> list[AssessmentProfileStatsResponse]:
    stats = await request.app.state.get_assessment_stats.execute()
    return [AssessmentProfileStatsResponse.from_domain(a) for a in stats]


@router.get("/advisor/snapshot", response_model=SnapshotResponse)
async def snapshot(_: SuperAdmin, request: Request) -> SnapshotResponse:
    result = await request.app.state.build_snapshot.execute()
    return SnapshotResponse(hash=result.hash, data=result.data)


@router.post("/advisor/ask", response_model=AdvisorQueryResponse)
async def ask(body: AskRequest, admin: SuperAdmin, request: Request) -> AdvisorQueryResponse:
    try:
        query = await request.app.state.ask_advisor.execute(admin.id, body.question)
    except InvalidQuestion as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Pregunta inválida") from exc
    except AdvisorUnavailable as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            str(exc) or "El asesor IA no está disponible en este momento.",
        ) from exc
    return AdvisorQueryResponse.from_domain(query)


@router.get("/advisor/history", response_model=list[AdvisorQueryResponse])
async def history(_: SuperAdmin, request: Request) -> list[AdvisorQueryResponse]:
    queries = await request.app.state.list_advisor_history.execute(50)
    return [AdvisorQueryResponse.from_domain(q) for q in queries]
