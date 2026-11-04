from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

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
from unsa_audit.learning.application.generators import generate_spec
from unsa_audit.learning.application.ports import (
    ContentSource,
    LearningRepository,
    UniversityFacts,
)
from unsa_audit.learning.domain.exercises import (
    ItemFeedback,
    Spec,
    grade,
    to_public,
    validate_spec,
)
from unsa_audit.learning.domain.progress import (
    credited_minutes,
    module_status,
    route_completed,
    route_status,
)
from unsa_audit.learning.domain.route import (
    Enrollment,
    EnrollmentStatus,
    ExerciseAttempt,
    Module,
    ModuleProgress,
    ModuleStatus,
    Route,
    RouteStatus,
)

Clock = Callable[[], datetime]


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _hours(minutes: int) -> float:
    return round(minutes / 60, 1)


# ----------------------------------------------------------------------------- vistas


@dataclass(frozen=True)
class RouteSummary:
    route: Route
    status: RouteStatus
    modules_total: int
    modules_completed: int
    minutes_credited: int
    modules_planned: int = 0

    @property
    def hours_credited(self) -> float:
        return _hours(self.minutes_credited)


@dataclass(frozen=True)
class RouteListing:
    routes: list[RouteSummary]
    total_hours_credited: float


@dataclass(frozen=True)
class ModuleSummary:
    module: Module
    status: ModuleStatus
    best_score: int | None


@dataclass(frozen=True)
class RouteDetail:
    summary: RouteSummary
    modules: list[ModuleSummary]


@dataclass(frozen=True)
class ModuleView:
    module: Module
    status: ModuleStatus
    best_score: int | None
    public_exercise: Spec | None


@dataclass(frozen=True)
class AttemptResult:
    score: int
    passed: bool
    pass_score: int
    items: tuple[ItemFeedback, ...]
    module_completed: bool
    route_completed: bool


@dataclass(frozen=True)
class CompletionResult:
    module_completed: bool
    route_completed: bool


# ----------------------------------------------------------------------------- consultas


class ListRoutes:
    def __init__(self, repo: LearningRepository) -> None:
        self._repo = repo

    async def execute(self, user_id: UUID) -> RouteListing:
        routes = await self._repo.list_routes()
        modules = await self._repo.list_modules()
        enrollments = {e.route_code: e for e in await self._repo.list_enrollments(user_id)}
        progress = await self._repo.list_progress(user_id)
        completed = {mid for mid, p in progress.items() if p.completed}

        summaries: list[RouteSummary] = []
        for route in sorted(routes, key=lambda r: r.order):
            route_modules = [m for m in modules if m.route_code == route.code]
            prerequisite = enrollments.get(route.prerequisite_code or "")
            summaries.append(
                RouteSummary(
                    route=route,
                    status=route_status(route, enrollments.get(route.code), prerequisite),
                    modules_total=sum(not m.planned for m in route_modules),
                    modules_completed=sum(m.id in completed for m in route_modules),
                    modules_planned=sum(m.planned for m in route_modules),
                    minutes_credited=credited_minutes(route_modules, completed),
                )
            )
        return RouteListing(summaries, _hours(sum(s.minutes_credited for s in summaries)))


class GetRoute:
    def __init__(self, repo: LearningRepository) -> None:
        self._repo = repo

    async def execute(self, user_id: UUID, code: str) -> RouteDetail:
        route = await self._repo.get_route(code)
        if route is None:
            raise RouteNotFound
        route_modules = await self._repo.list_modules(code)
        enrollment = await self._repo.get_enrollment(user_id, code)
        prerequisite = (
            await self._repo.get_enrollment(user_id, route.prerequisite_code)
            if route.prerequisite_code
            else None
        )
        progress = await self._repo.list_progress(user_id)
        completed = {mid for mid, p in progress.items() if p.completed}
        summary = RouteSummary(
            route=route,
            status=route_status(route, enrollment, prerequisite),
            modules_total=sum(not m.planned for m in route_modules),
            modules_completed=sum(m.id in completed for m in route_modules),
            modules_planned=sum(m.planned for m in route_modules),
            minutes_credited=credited_minutes(route_modules, completed),
        )
        modules = [
            ModuleSummary(
                module=m,
                status=module_status(m, route_modules, completed, enrollment is not None),
                best_score=progress[m.id].best_score if m.id in progress else None,
            )
            for m in route_modules
        ]
        return RouteDetail(summary, modules)


# ----------------------------------------------------------------------------- matricula


class EnrollInRoute:
    def __init__(self, repo: LearningRepository, clock: Clock = _utcnow) -> None:
        self._repo = repo
        self._clock = clock

    async def execute(self, user_id: UUID, code: str) -> tuple[Enrollment, bool]:
        """Devuelve (matricula, creada). Idempotente si ya estaba matriculado."""
        route = await self._repo.get_route(code)
        if route is None:
            raise RouteNotFound
        existing = await self._repo.get_enrollment(user_id, code)
        if existing is not None:
            return existing, False
        if route.prerequisite_code:
            prerequisite = await self._repo.get_enrollment(user_id, route.prerequisite_code)
            if prerequisite is None or prerequisite.status is not EnrollmentStatus.COMPLETED:
                raise PrerequisiteNotMet(route.prerequisite_code)
        enrollment = Enrollment(user_id, code, EnrollmentStatus.IN_PROGRESS, self._clock())
        await self._repo.save_enrollment(enrollment)
        return enrollment, True


# ----------------------------------------------------------------------------- modulos


class _ModuleContext:
    """Carga lo necesario para decidir sobre un modulo: ruta, matricula y progreso."""

    def __init__(self, repo: LearningRepository) -> None:
        self._repo = repo

    async def load(self, user_id: UUID, module_id: UUID):
        module = await self._repo.get_module(module_id)
        if module is None:
            raise ModuleNotFound
        if module.planned:
            raise ModulePlanned
        enrollment = await self._repo.get_enrollment(user_id, module.route_code)
        if enrollment is None:
            raise NotEnrolled
        route_modules = await self._repo.list_modules(module.route_code)
        progress = await self._repo.list_progress(user_id)
        completed = {mid for mid, p in progress.items() if p.completed}
        if module_status(module, route_modules, completed, True) is ModuleStatus.LOCKED:
            raise ModuleLocked
        return module, enrollment, route_modules, progress, completed


async def _resolve_spec(module: Module, facts: UniversityFacts) -> Spec:
    assert module.exercise is not None
    if module.exercise.generator:
        spec = generate_spec(
            module.exercise.generator, module.exercise.params, await facts.snapshot()
        )
    else:
        spec = module.exercise.spec
    validate_spec(module.exercise.kind, spec)
    return spec


class GetModule:
    def __init__(self, repo: LearningRepository, facts: UniversityFacts) -> None:
        self._ctx = _ModuleContext(repo)
        self._facts = facts

    async def execute(self, user_id: UUID, module_id: UUID) -> ModuleView:
        module, _, route_modules, progress, completed = await self._ctx.load(user_id, module_id)
        public = None
        if module.exercise is not None:
            spec = await _resolve_spec(module, self._facts)
            public = to_public(module.exercise.kind, spec, seed=str(module.id))
        return ModuleView(
            module=module,
            status=module_status(module, route_modules, completed, True),
            best_score=progress[module.id].best_score if module.id in progress else None,
            public_exercise=public,
        )


class SubmitAttempt:
    def __init__(
        self,
        repo: LearningRepository,
        facts: UniversityFacts,
        clock: Clock = _utcnow,
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._repo = repo
        self._ctx = _ModuleContext(repo)
        self._facts = facts
        self._clock = clock
        self._id_factory = id_factory

    async def execute(self, user_id: UUID, module_id: UUID, answer: Any) -> AttemptResult:
        module, enrollment, route_modules, progress, completed = await self._ctx.load(
            user_id, module_id
        )
        if module.exercise is None:
            raise NoExercise
        spec = await _resolve_spec(module, self._facts)
        result = grade(module.exercise.kind, spec, answer)  # InvalidAnswer si la forma es mala
        passed = result.score >= module.exercise.pass_score
        now = self._clock()

        await self._repo.add_attempt(
            ExerciseAttempt(
                self._id_factory(), user_id, module_id, answer, result.score, passed, now
            )
        )

        previous = progress.get(module.id)
        was_completed = module.id in completed
        is_completed = was_completed or passed
        await self._repo.save_progress(
            ModuleProgress(
                user_id=user_id,
                module_id=module.id,
                best_score=max(previous.best_score if previous else 0, result.score),
                completed=is_completed,
                minutes_credited=module.minutes if is_completed else 0,
                completed_at=(
                    previous.completed_at
                    if was_completed and previous
                    else (now if passed else None)
                ),
            )
        )
        if is_completed:
            completed = completed | {module.id}
        route_done = route_completed(route_modules, completed)
        if route_done and enrollment.status is not EnrollmentStatus.COMPLETED:
            await self._repo.save_enrollment(
                Enrollment(
                    user_id,
                    enrollment.route_code,
                    EnrollmentStatus.COMPLETED,
                    enrollment.started_at,
                    now,
                )  # fmt: skip
            )
        return AttemptResult(
            score=result.score,
            passed=passed,
            pass_score=module.exercise.pass_score,
            items=result.items,
            module_completed=is_completed,
            route_completed=route_done,
        )


class CompleteReadingModule:
    def __init__(self, repo: LearningRepository, clock: Clock = _utcnow) -> None:
        self._repo = repo
        self._ctx = _ModuleContext(repo)
        self._clock = clock

    async def execute(self, user_id: UUID, module_id: UUID) -> CompletionResult:
        module, enrollment, route_modules, progress, completed = await self._ctx.load(
            user_id, module_id
        )
        if module.exercise is not None:
            raise HasExercise
        now = self._clock()
        if module.id not in completed:
            await self._repo.save_progress(
                ModuleProgress(user_id, module.id, 100, True, module.minutes, now)
            )
            completed = completed | {module.id}
        route_done = route_completed(route_modules, completed)
        if route_done and enrollment.status is not EnrollmentStatus.COMPLETED:
            await self._repo.save_enrollment(
                Enrollment(
                    user_id,
                    enrollment.route_code,
                    EnrollmentStatus.COMPLETED,
                    enrollment.started_at,
                    now,
                )  # fmt: skip
            )
        return CompletionResult(module_completed=True, route_completed=route_done)


# ----------------------------------------------------------------------------- contenido


class SyncContent:
    def __init__(self, repo: LearningRepository, source: ContentSource) -> None:
        self._repo = repo
        self._source = source

    async def execute(self) -> tuple[int, int]:
        routes, modules = self._source.load()
        await self._repo.replace_content(routes, modules)
        return len(routes), len(modules)
