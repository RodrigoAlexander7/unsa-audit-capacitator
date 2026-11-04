from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel

from unsa_audit.identity.interface.dependencies import CurrentUser
from unsa_audit.learning.application.errors import (
    HasExercise,
    ModuleLocked,
    ModuleNotFound,
    ModulePlanned,
    NoExercise,
    NotEnrolled,
    PrerequisiteNotMet,
    RouteNotFound,
)
from unsa_audit.learning.application.use_cases import (
    AttemptResult,
    ModuleView,
    RouteDetail,
    RouteSummary,
)
from unsa_audit.learning.domain.exercises import InvalidAnswer
from unsa_audit.learning.domain.route import Enrollment

router = APIRouter(tags=["learning"])


# ----------------------------------------------------------------------------- schemas


class RouteSummaryResponse(BaseModel):
    code: str
    order: int
    title: str
    description: str
    hours: int
    prerequisite_code: str | None
    status: str
    modules_total: int
    modules_completed: int
    modules_planned: int
    minutes_credited: int
    hours_credited: float

    @classmethod
    def from_domain(cls, s: RouteSummary) -> "RouteSummaryResponse":
        r = s.route
        return cls(
            code=r.code,
            order=r.order,
            title=r.title,
            description=r.description,
            hours=r.hours,
            prerequisite_code=r.prerequisite_code,
            status=s.status.value,
            modules_total=s.modules_total,
            modules_completed=s.modules_completed,
            modules_planned=s.modules_planned,
            minutes_credited=s.minutes_credited,
            hours_credited=s.hours_credited,
        )


class RoutesResponse(BaseModel):
    routes: list[RouteSummaryResponse]
    total_hours_credited: float


class ModuleSummaryResponse(BaseModel):
    id: str
    order: int
    title: str
    minutes: int
    mandatory: bool
    is_final: bool
    has_exercise: bool
    planned: bool
    status: str
    best_score: int | None


class RouteDetailResponse(BaseModel):
    route: RouteSummaryResponse
    modules: list[ModuleSummaryResponse]

    @classmethod
    def from_domain(cls, d: RouteDetail) -> "RouteDetailResponse":
        return cls(
            route=RouteSummaryResponse.from_domain(d.summary),
            modules=[
                ModuleSummaryResponse(
                    id=str(m.module.id),
                    order=m.module.order,
                    title=m.module.title,
                    minutes=m.module.minutes,
                    mandatory=m.module.mandatory,
                    is_final=m.module.is_final,
                    has_exercise=m.module.exercise is not None,
                    planned=m.module.planned,
                    status=m.status.value,
                    best_score=m.best_score,
                )
                for m in d.modules
            ],
        )


class EnrollmentResponse(BaseModel):
    route_code: str
    status: str
    started_at: datetime
    completed_at: datetime | None

    @classmethod
    def from_domain(cls, e: Enrollment) -> "EnrollmentResponse":
        return cls(
            route_code=e.route_code,
            status=e.status.value,
            started_at=e.started_at,
            completed_at=e.completed_at,
        )


class ExercisePublic(BaseModel):
    kind: str
    pass_score: int
    spec: dict[str, Any]


class ModuleResponse(BaseModel):
    id: str
    route_code: str
    title: str
    minutes: int
    is_final: bool
    status: str
    best_score: int | None
    lesson_md: str
    exercise: ExercisePublic | None

    @classmethod
    def from_domain(cls, v: ModuleView) -> "ModuleResponse":
        m = v.module
        exercise = None
        if m.exercise is not None and v.public_exercise is not None:
            exercise = ExercisePublic(
                kind=m.exercise.kind.value,
                pass_score=m.exercise.pass_score,
                spec=v.public_exercise,
            )
        return cls(
            id=str(m.id),
            route_code=m.route_code,
            title=m.title,
            minutes=m.minutes,
            is_final=m.is_final,
            status=v.status.value,
            best_score=v.best_score,
            lesson_md=m.lesson_md,
            exercise=exercise,
        )


class AttemptRequest(BaseModel):
    answer: dict[str, Any]


class ItemFeedbackResponse(BaseModel):
    id: str
    correct: bool
    feedback: str


class AttemptResponse(BaseModel):
    score: int
    passed: bool
    pass_score: int
    items: list[ItemFeedbackResponse]
    module_completed: bool
    route_completed: bool

    @classmethod
    def from_domain(cls, r: AttemptResult) -> "AttemptResponse":
        return cls(
            score=r.score,
            passed=r.passed,
            pass_score=r.pass_score,
            items=[ItemFeedbackResponse(id=i.id, correct=i.correct, feedback=i.feedback)
                   for i in r.items],
            module_completed=r.module_completed,
            route_completed=r.route_completed,
        )  # fmt: skip


class CompletionResponse(BaseModel):
    module_completed: bool
    route_completed: bool


# ----------------------------------------------------------------------------- errores

_NOT_ENROLLED = HTTPException(status.HTTP_403_FORBIDDEN, "No estás matriculado en esta ruta")


def _module_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ModuleNotFound):
        return HTTPException(status.HTTP_404_NOT_FOUND, "Módulo no encontrado")
    if isinstance(exc, NotEnrolled):
        return _NOT_ENROLLED
    if isinstance(exc, ModulePlanned):
        return HTTPException(status.HTTP_409_CONFLICT, "Este módulo está en preparación")
    if isinstance(exc, ModuleLocked):
        return HTTPException(
            status.HTTP_409_CONFLICT, "Completa antes los demás módulos de la ruta"
        )
    if isinstance(exc, NoExercise):
        return HTTPException(status.HTTP_409_CONFLICT, "Este módulo no tiene ejercicio")
    if isinstance(exc, HasExercise):
        return HTTPException(status.HTTP_409_CONFLICT, "Este módulo se completa con su ejercicio")
    if isinstance(exc, InvalidAnswer):
        return HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc))
    raise exc


# ----------------------------------------------------------------------------- endpoints


@router.get("/routes", response_model=RoutesResponse)
async def list_routes(user: CurrentUser, request: Request) -> RoutesResponse:
    listing = await request.app.state.list_routes.execute(user.id)
    return RoutesResponse(
        routes=[RouteSummaryResponse.from_domain(s) for s in listing.routes],
        total_hours_credited=listing.total_hours_credited,
    )


@router.get("/routes/{code}", response_model=RouteDetailResponse)
async def get_route(code: str, user: CurrentUser, request: Request) -> RouteDetailResponse:
    try:
        detail = await request.app.state.get_route.execute(user.id, code)
    except RouteNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ruta no encontrada") from exc
    return RouteDetailResponse.from_domain(detail)


@router.post("/routes/{code}/enroll", response_model=EnrollmentResponse, status_code=201)
async def enroll(
    code: str, user: CurrentUser, request: Request, response: Response
) -> EnrollmentResponse:
    try:
        enrollment, created = await request.app.state.enroll_in_route.execute(user.id, code)
    except RouteNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ruta no encontrada") from exc
    except PrerequisiteNotMet as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {
                "code": "prerequisite_not_met",
                "message": "Debes aprobar la ruta anterior antes de matricularte.",
                "prerequisite": exc.prerequisite_code,
            },
        ) from exc
    if not created:
        response.status_code = status.HTTP_200_OK
    return EnrollmentResponse.from_domain(enrollment)


@router.get("/modules/{module_id}", response_model=ModuleResponse)
async def get_module(module_id: UUID, user: CurrentUser, request: Request) -> ModuleResponse:
    try:
        view = await request.app.state.get_module.execute(user.id, module_id)
    except (ModuleNotFound, NotEnrolled, ModuleLocked, ModulePlanned) as exc:
        raise _module_error(exc) from exc
    return ModuleResponse.from_domain(view)


@router.post("/modules/{module_id}/attempts", response_model=AttemptResponse)
async def submit_attempt(
    module_id: UUID, body: AttemptRequest, user: CurrentUser, request: Request
) -> AttemptResponse:
    try:
        result = await request.app.state.submit_attempt.execute(user.id, module_id, body.answer)
    except (
        ModuleNotFound,
        NotEnrolled,
        ModuleLocked,
        ModulePlanned,
        NoExercise,
        InvalidAnswer,
    ) as exc:
        raise _module_error(exc) from exc
    return AttemptResponse.from_domain(result)


@router.post("/modules/{module_id}/complete", response_model=CompletionResponse)
async def complete_module(
    module_id: UUID, user: CurrentUser, request: Request
) -> CompletionResponse:
    try:
        result = await request.app.state.complete_reading.execute(user.id, module_id)
    except (ModuleNotFound, NotEnrolled, ModuleLocked, ModulePlanned, HasExercise) as exc:
        raise _module_error(exc) from exc
    return CompletionResponse(
        module_completed=result.module_completed, route_completed=result.route_completed
    )
