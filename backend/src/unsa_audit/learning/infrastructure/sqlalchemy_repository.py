from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from unsa_audit.learning.domain.route import (
    Enrollment,
    EnrollmentStatus,
    ExerciseAttempt,
    ExerciseDef,
    ExerciseKind,
    Module,
    ModuleProgress,
    Route,
)
from unsa_audit.learning.infrastructure.models import (
    EnrollmentModel,
    ExerciseAttemptModel,
    ModuleModel,
    ModuleProgressModel,
    RouteModel,
)


def _route(m: RouteModel) -> Route:
    return Route(m.code, m.order, m.title, m.description, m.hours, m.prerequisite_code)


def _module(m: ModuleModel) -> Module:
    exercise = None
    if m.exercise_kind:
        exercise = ExerciseDef(
            kind=ExerciseKind(m.exercise_kind),
            spec=m.exercise_spec or {},
            generator=m.exercise_generator,
            params=m.exercise_params or {},
            pass_score=m.pass_score,
        )
    return Module(
        id=m.id,
        route_code=m.route_code,
        slug=m.slug,
        order=m.order,
        title=m.title,
        minutes=m.minutes,
        mandatory=m.mandatory,
        is_final=m.is_final,
        planned=m.planned,
        lesson_md=m.lesson_md,
        exercise=exercise,
        reference_title=m.reference_title,
        reference_md=m.reference_md,
    )


def _enrollment(m: EnrollmentModel) -> Enrollment:
    return Enrollment(
        m.user_id, m.route_code, EnrollmentStatus(m.status), m.started_at, m.completed_at
    )


class SqlAlchemyLearningRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    # ------------------------------------------------------------------ contenido

    async def replace_content(self, routes: list[Route], modules: list[Module]) -> None:
        async with self._sf() as session, session.begin():
            for route in sorted(routes, key=lambda r: r.order):  # prerrequisito antes
                row = await session.get(RouteModel, route.code)
                if row is None:
                    row = RouteModel(code=route.code)
                    session.add(row)
                row.order = route.order
                row.title = route.title
                row.description = route.description
                row.hours = route.hours
                row.prerequisite_code = route.prerequisite_code
                await session.flush()

            wanted = {m.id for m in modules}
            existing = {m.id: m for m in await session.scalars(select(ModuleModel))}
            stale = [mid for mid in existing if mid not in wanted]
            if stale:
                await session.execute(delete(ModuleModel).where(ModuleModel.id.in_(stale)))
            for module in modules:
                row = existing.get(module.id)
                if row is None:
                    row = ModuleModel(id=module.id)
                    session.add(row)
                ex = module.exercise
                row.route_code = module.route_code
                row.slug = module.slug
                row.order = module.order
                row.title = module.title
                row.minutes = module.minutes
                row.mandatory = module.mandatory
                row.is_final = module.is_final
                row.planned = module.planned
                row.lesson_md = module.lesson_md
                row.reference_title = module.reference_title
                row.reference_md = module.reference_md
                row.exercise_kind = ex.kind.value if ex else None
                row.exercise_spec = ex.spec if ex else {}
                row.exercise_generator = ex.generator if ex else None
                row.exercise_params = ex.params if ex else {}
                row.pass_score = ex.pass_score if ex else 70

    # ------------------------------------------------------------------ catalogo

    async def list_routes(self) -> list[Route]:
        async with self._sf() as session:
            rows = await session.scalars(select(RouteModel).order_by(RouteModel.order))
            return [_route(r) for r in rows]

    async def get_route(self, code: str) -> Route | None:
        async with self._sf() as session:
            row = await session.get(RouteModel, code)
            return _route(row) if row else None

    async def list_modules(self, route_code: str | None = None) -> list[Module]:
        async with self._sf() as session:
            query = select(ModuleModel).order_by(ModuleModel.route_code, ModuleModel.order)
            if route_code is not None:
                query = query.where(ModuleModel.route_code == route_code)
            return [_module(m) for m in await session.scalars(query)]

    async def get_module(self, module_id: UUID) -> Module | None:
        async with self._sf() as session:
            row = await session.get(ModuleModel, module_id)
            return _module(row) if row else None

    # ------------------------------------------------------------------ matriculas

    async def get_enrollment(self, user_id: UUID, route_code: str) -> Enrollment | None:
        async with self._sf() as session:
            row = await session.get(EnrollmentModel, (user_id, route_code))
            return _enrollment(row) if row else None

    async def list_enrollments(self, user_id: UUID) -> list[Enrollment]:
        async with self._sf() as session:
            rows = await session.scalars(
                select(EnrollmentModel).where(EnrollmentModel.user_id == user_id)
            )
            return [_enrollment(r) for r in rows]

    async def save_enrollment(self, enrollment: Enrollment) -> None:
        async with self._sf() as session, session.begin():
            row = await session.get(EnrollmentModel, (enrollment.user_id, enrollment.route_code))
            if row is None:
                row = EnrollmentModel(user_id=enrollment.user_id, route_code=enrollment.route_code)
                session.add(row)
            row.status = enrollment.status.value
            row.started_at = enrollment.started_at
            row.completed_at = enrollment.completed_at

    # ------------------------------------------------------------------ progreso

    async def list_progress(self, user_id: UUID) -> dict[UUID, ModuleProgress]:
        async with self._sf() as session:
            rows = await session.scalars(
                select(ModuleProgressModel).where(ModuleProgressModel.user_id == user_id)
            )
            return {
                r.module_id: ModuleProgress(
                    r.user_id,
                    r.module_id,
                    r.best_score,
                    r.completed,
                    r.minutes_credited,
                    r.completed_at,
                )  # fmt: skip
                for r in rows
            }

    async def save_progress(self, progress: ModuleProgress) -> None:
        async with self._sf() as session, session.begin():
            row = await session.get(ModuleProgressModel, (progress.user_id, progress.module_id))
            if row is None:
                row = ModuleProgressModel(user_id=progress.user_id, module_id=progress.module_id)
                session.add(row)
            row.best_score = progress.best_score
            row.completed = progress.completed
            row.minutes_credited = progress.minutes_credited
            row.completed_at = progress.completed_at

    async def add_attempt(self, attempt: ExerciseAttempt) -> None:
        async with self._sf() as session, session.begin():
            session.add(
                ExerciseAttemptModel(
                    id=attempt.id,
                    user_id=attempt.user_id,
                    module_id=attempt.module_id,
                    answer=attempt.answer,
                    score=attempt.score,
                    passed=attempt.passed,
                    created_at=attempt.created_at,
                )
            )

    async def count_attempts(self, user_id: UUID, module_id: UUID) -> int:
        async with self._sf() as session:
            result = await session.scalar(
                select(func.count())
                .select_from(ExerciseAttemptModel)
                .where(
                    ExerciseAttemptModel.user_id == user_id,
                    ExerciseAttemptModel.module_id == module_id,
                )
            )
            return int(result or 0)
