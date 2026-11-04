"""Lecturas agregadas en SQL: nunca se cargan filas de personas (anonimato por construccion)."""

from collections import defaultdict
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, case, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from unsa_audit.analytics.domain.stats import (
    STALLED_DAYS,
    AdvisorQuery,
    AssessmentProfileStats,
    GroupAverage,
    ModuleStats,
    ParticipantCounts,
    RouteStats,
    percent,
)
from unsa_audit.analytics.infrastructure.models import AdvisorQueryModel
from unsa_audit.assessment.infrastructure.models import AssessmentModel
from unsa_audit.identity.infrastructure.models import UserModel
from unsa_audit.learning.infrastructure.models import (
    EnrollmentModel,
    ExerciseAttemptModel,
    ModuleModel,
    ModuleProgressModel,
    RouteModel,
)

_LEARNER = UserModel.role == "learner"


class SqlAlchemyAnalyticsRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    async def route_stats(self, now: datetime) -> list[RouteStats]:
        cutoff = now - timedelta(days=STALLED_DAYS)
        async with self._sf() as session:
            routes = (await session.scalars(select(RouteModel).order_by(RouteModel.order))).all()
            published = dict(
                (
                    await session.execute(
                        select(ModuleModel.route_code, func.count())
                        .where(ModuleModel.planned.is_(False))
                        .group_by(ModuleModel.route_code)
                    )
                ).all()
            )
            enrollments: dict[tuple[str, str], int] = {
                (code, st): n
                for code, st, n in (
                    await session.execute(
                        select(EnrollmentModel.route_code, EnrollmentModel.status, func.count())
                        .join(UserModel, UserModel.id == EnrollmentModel.user_id)
                        .where(_LEARNER)
                        .group_by(EnrollmentModel.route_code, EnrollmentModel.status)
                    )
                ).all()
            }
            progress = {
                code: (done, minutes)
                for code, done, minutes in (
                    await session.execute(
                        select(
                            ModuleModel.route_code,
                            func.count(),
                            func.coalesce(func.sum(ModuleProgressModel.minutes_credited), 0),
                        )
                        .join(ModuleModel, ModuleModel.id == ModuleProgressModel.module_id)
                        .join(UserModel, UserModel.id == ModuleProgressModel.user_id)
                        .where(_LEARNER, ModuleProgressModel.completed.is_(True))
                        .group_by(ModuleModel.route_code)
                    )
                ).all()
            }
            attempts = {
                code: (total, passed)
                for code, total, passed in (
                    await session.execute(
                        select(
                            ModuleModel.route_code,
                            func.count(),
                            func.coalesce(
                                func.sum(case((ExerciseAttemptModel.passed.is_(True), 1), else_=0)),
                                0,
                            ),
                        )
                        .join(ModuleModel, ModuleModel.id == ExerciseAttemptModel.module_id)
                        .join(UserModel, UserModel.id == ExerciseAttemptModel.user_id)
                        .where(_LEARNER)
                        .group_by(ModuleModel.route_code)
                    )
                ).all()
            }
            recent = (
                select(ExerciseAttemptModel.id)
                .join(ModuleModel, ModuleModel.id == ExerciseAttemptModel.module_id)
                .where(
                    ExerciseAttemptModel.user_id == EnrollmentModel.user_id,
                    ModuleModel.route_code == EnrollmentModel.route_code,
                    ExerciseAttemptModel.created_at >= cutoff,
                )
            )
            stalled = dict(
                (
                    await session.execute(
                        select(EnrollmentModel.route_code, func.count())
                        .join(UserModel, UserModel.id == EnrollmentModel.user_id)
                        .where(_LEARNER, EnrollmentModel.status == "in_progress", ~exists(recent))
                        .group_by(EnrollmentModel.route_code)
                    )
                ).all()
            )

        result: list[RouteStats] = []
        for r in routes:
            in_progress = enrollments.get((r.code, "in_progress"), 0)
            completed = enrollments.get((r.code, "completed"), 0)
            enrolled = in_progress + completed
            modules_total = published.get(r.code, 0)
            done, minutes = progress.get(r.code, (0, 0))
            total_attempts, passed = attempts.get(r.code, (0, 0))
            result.append(
                RouteStats(
                    code=r.code,
                    order=r.order,
                    title=r.title,
                    hours=r.hours,
                    modules_total=modules_total,
                    enrolled=enrolled,
                    in_progress=in_progress,
                    completed=completed,
                    completion_rate=percent(completed, enrolled),
                    avg_progress=percent(done, enrolled * modules_total),
                    avg_hours_credited=round(minutes / 60 / enrolled, 1) if enrolled else 0.0,
                    attempts=total_attempts,
                    pass_rate=percent(passed, total_attempts),
                    stalled=stalled.get(r.code, 0),
                )
            )
        return result

    async def module_stats(self, route_code: str | None = None) -> list[ModuleStats]:
        async with self._sf() as session:
            query = select(ModuleModel).where(ModuleModel.planned.is_(False))
            if route_code is not None:
                query = query.where(ModuleModel.route_code == route_code)
            modules = (
                await session.scalars(query.order_by(ModuleModel.route_code, ModuleModel.order))
            ).all()

            attempt_rows = {
                mid: (total, users, avg, passed)
                for mid, total, users, avg, passed in (
                    await session.execute(
                        select(
                            ExerciseAttemptModel.module_id,
                            func.count(),
                            func.count(func.distinct(ExerciseAttemptModel.user_id)),
                            func.avg(ExerciseAttemptModel.score),
                            func.coalesce(
                                func.sum(case((ExerciseAttemptModel.passed.is_(True), 1), else_=0)),
                                0,
                            ),
                        )
                        .join(UserModel, UserModel.id == ExerciseAttemptModel.user_id)
                        .where(_LEARNER)
                        .group_by(ExerciseAttemptModel.module_id)
                    )
                ).all()
            }
            completed_rows = dict(
                (
                    await session.execute(
                        select(ModuleProgressModel.module_id, func.count())
                        .join(UserModel, UserModel.id == ModuleProgressModel.user_id)
                        .where(_LEARNER, ModuleProgressModel.completed.is_(True))
                        .group_by(ModuleProgressModel.module_id)
                    )
                ).all()
            )

        result: list[ModuleStats] = []
        for m in modules:
            total, users, avg, passed = attempt_rows.get(m.id, (0, 0, None, 0))
            result.append(
                ModuleStats(
                    id=m.id,
                    route_code=m.route_code,
                    order=m.order,
                    title=m.title,
                    minutes=m.minutes,
                    is_final=m.is_final,
                    attempts=total,
                    learners_attempted=users,
                    learners_completed=completed_rows.get(m.id, 0),
                    avg_score=int(round(float(avg))) if avg is not None else None,
                    pass_rate=percent(passed, total) if total else None,
                )
            )
        return result

    async def assessment_stats(self) -> list[AssessmentProfileStats]:
        async with self._sf() as session:
            rows = (
                await session.execute(
                    select(AssessmentModel.profile, AssessmentModel.score, AssessmentModel.passed,
                           AssessmentModel.result)
                    .join(UserModel, UserModel.id == AssessmentModel.user_id)
                    .where(_LEARNER, AssessmentModel.status == "finished")
                    .order_by(AssessmentModel.profile)
                )
            ).all()  # fmt: skip

        by_profile: dict[str, list[tuple[int, bool, dict]]] = defaultdict(list)
        for profile, score, passed, result in rows:
            by_profile[profile].append((score or 0, bool(passed), result or {}))

        stats: list[AssessmentProfileStats] = []
        for profile, items in sorted(by_profile.items()):
            finished = len(items)
            stats.append(
                AssessmentProfileStats(
                    profile=profile,
                    finished=finished,
                    avg_score=percent(sum(s for s, _, _ in items), finished * 100),
                    pass_rate=percent(sum(p for _, p, _ in items), finished),
                    competencies=_groups(items, "competencies"),
                    requirements=_groups(items, "requirements"),
                )
            )
        return stats

    async def participants(self, now: datetime) -> ParticipantCounts:
        async with self._sf() as session:
            total = await session.scalar(
                select(func.count()).select_from(UserModel).where(_LEARNER)
            )
            recent = await session.scalar(
                select(func.count())
                .select_from(UserModel)
                .where(and_(_LEARNER, UserModel.created_at >= now - timedelta(days=7)))
            )
            return ParticipantCounts(total or 0, recent or 0)


def _groups(items: list[tuple[int, bool, dict]], key: str) -> list[GroupAverage]:
    """Acumula aciertos/total por grupo (competencia o requisito) entre evaluaciones."""
    totals: dict[str, list[int]] = {}
    labels: dict[str, str] = {}
    for _, _, result in items:
        for group in result.get(key, []):
            acc = totals.setdefault(group["key"], [0, 0, 0])
            acc[0] += group["correct"]
            acc[1] += group["total"]
            acc[2] += 1
            labels[group["key"]] = group["label"]
    groups = [GroupAverage(k, labels[k], percent(c, t), n) for k, (c, t, n) in totals.items()]
    return sorted(groups, key=lambda g: (g.average, g.label))  # peores primero


class SqlAlchemyAdvisorQueryRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    async def add(self, query: AdvisorQuery) -> None:
        async with self._sf() as session, session.begin():
            session.add(
                AdvisorQueryModel(
                    id=query.id,
                    asked_by=query.asked_by,
                    question=query.question,
                    snapshot_hash=query.snapshot_hash,
                    status=query.status,
                    answer=query.answer,
                    error=query.error,
                    duration_ms=query.duration_ms,
                    created_at=query.created_at,
                )
            )

    async def list_recent(self, limit: int) -> list[AdvisorQuery]:
        async with self._sf() as session:
            rows = await session.scalars(
                select(AdvisorQueryModel).order_by(AdvisorQueryModel.created_at.desc()).limit(limit)
            )
            return [
                AdvisorQuery(
                    id=r.id,
                    asked_by=r.asked_by,
                    question=r.question,
                    snapshot_hash=r.snapshot_hash,
                    status=r.status,
                    answer=r.answer,
                    error=r.error,
                    duration_ms=r.duration_ms,
                    created_at=r.created_at,
                )
                for r in rows
            ]


__all__ = ["SqlAlchemyAdvisorQueryRepository", "SqlAlchemyAnalyticsRepository", "UUID"]
