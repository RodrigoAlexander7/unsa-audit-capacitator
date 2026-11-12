"""Proveedor SQLAlchemy del cohorte seudonimizado para el modo administrador."""

from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from unsa_audit.analytics.application.ports import AnalyticsReadRepository, PimsSummaryProvider
from unsa_audit.analytics.domain.stats import STALLED_DAYS, hardest_modules, percent
from unsa_audit.assessment.infrastructure.models import AssessmentModel
from unsa_audit.assistant.domain.admin_cohort import AdminCohortSnapshot, LearnerAliasRecord
from unsa_audit.identity.infrastructure.models import UserModel
from unsa_audit.learning.infrastructure.models import (
    EnrollmentModel,
    ExerciseAttemptModel,
    ModuleModel,
    ModuleProgressModel,
    RouteModel,
)


def _utcnow() -> datetime:
    return datetime.now(UTC)


class SqlAlchemyAdminCohortProvider:
    """Construye alias P-01, P-02... y metricas de cohorte sin enviar PII a la IA."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        analytics: AnalyticsReadRepository,
        pims: PimsSummaryProvider,
        clock: Callable[[], datetime] = _utcnow,
    ) -> None:
        self._sf = session_factory
        self._analytics = analytics
        self._pims = pims
        self._clock = clock

    async def snapshot(self) -> AdminCohortSnapshot:
        now = self._clock()
        cutoff = now - timedelta(days=STALLED_DAYS)

        async with self._sf() as session:
            users = (
                await session.scalars(
                    select(UserModel)
                    .where(UserModel.role == "learner")
                    .order_by(UserModel.email, UserModel.id)
                )
            ).all()
            routes = (await session.scalars(select(RouteModel).order_by(RouteModel.order))).all()
            modules = (
                await session.scalars(select(ModuleModel).where(ModuleModel.planned.is_(False)))
            ).all()
            enrollments = (await session.scalars(select(EnrollmentModel))).all()
            progress_rows = (await session.scalars(select(ModuleProgressModel))).all()
            attempt_rows = (
                await session.execute(
                    select(
                        ExerciseAttemptModel.user_id,
                        ExerciseAttemptModel.module_id,
                        ExerciseAttemptModel.passed,
                        ExerciseAttemptModel.created_at,
                    )
                )
            ).all()
            assessment_rows = (
                await session.scalars(
                    select(AssessmentModel).where(AssessmentModel.status == "finished")
                )
            ).all()

        route_mod_count: dict[str, int] = defaultdict(int)
        mod_route: dict[UUID, str] = {}
        mod_slug: dict[UUID, str] = {}
        for mod in modules:
            route_mod_count[mod.route_code] += 1
            mod_route[mod.id] = mod.route_code
            mod_slug[mod.id] = mod.slug

        enr_by_user: dict[UUID, list[EnrollmentModel]] = defaultdict(list)
        for enr in enrollments:
            enr_by_user[enr.user_id].append(enr)

        done_by_user_route: dict[tuple[UUID, str], int] = defaultdict(int)
        minutes_by_user: dict[UUID, int] = defaultdict(int)
        for pr in progress_rows:
            if pr.completed:
                rc = mod_route.get(pr.module_id)
                if rc:
                    done_by_user_route[(pr.user_id, rc)] += 1
                minutes_by_user[pr.user_id] += pr.minutes_credited

        attempts_by_user: dict[UUID, int] = defaultdict(int)
        fails_by_user: dict[UUID, int] = defaultdict(int)
        last_activity_by_user: dict[UUID, datetime] = {}
        last_attempt_in_route: dict[tuple[UUID, str], datetime] = {}
        for uid, mid, passed, created_at in attempt_rows:
            attempts_by_user[uid] += 1
            if not passed:
                fails_by_user[uid] += 1
            prev = last_activity_by_user.get(uid)
            if prev is None or created_at > prev:
                last_activity_by_user[uid] = created_at
            rc = mod_route.get(mid)
            if rc:
                prev_r = last_attempt_in_route.get((uid, rc))
                if prev_r is None or created_at > prev_r:
                    last_attempt_in_route[(uid, rc)] = created_at

        assess_by_user: dict[UUID, list[dict[str, object]]] = defaultdict(list)
        for asm in assessment_rows:
            assess_by_user[asm.user_id].append(
                {
                    "profile": asm.profile,
                    "score_pct": asm.score,
                    "passed": bool(asm.passed),
                }
            )

        learners: list[LearnerAliasRecord] = []
        for idx, user in enumerate(users, start=1):
            alias = f"P-{idx:02d}"
            user_enr = sorted(enr_by_user.get(user.id, []), key=lambda e: e.route_code)
            route_items: list[dict[str, object]] = []
            stalled = False
            done_total = 0
            expected_total = 0
            latest_ts = last_activity_by_user.get(user.id)

            for enr in user_enr:
                total_r = route_mod_count.get(enr.route_code, 0)
                done_r = done_by_user_route.get((user.id, enr.route_code), 0)
                expected_total += total_r
                done_total += done_r
                route_items.append(
                    {
                        "route": enr.route_code,
                        "status": enr.status,
                        "completed_modules": done_r,
                        "total_modules": total_r,
                    }
                )
                if latest_ts is None or enr.started_at > latest_ts:
                    latest_ts = enr.started_at
                if enr.status == "in_progress":
                    last_r = last_attempt_in_route.get((user.id, enr.route_code))
                    ref_ts = last_r or enr.started_at
                    if ref_ts < cutoff:
                        stalled = True

            days_since = max(0, (now - latest_ts).days) if latest_ts is not None else None
            learners.append(
                LearnerAliasRecord(
                    user_id=user.id,
                    alias=alias,
                    full_name=user.full_name,
                    email=user.email,
                    stalled=stalled,
                    days_since_activity=days_since,
                    overall_progress_pct=percent(done_total, expected_total),
                    minutes_credited=minutes_by_user.get(user.id, 0),
                    attempts=attempts_by_user.get(user.id, 0),
                    failed_attempts=fails_by_user.get(user.id, 0),
                    routes=tuple(route_items),
                    assessments=tuple(assess_by_user.get(user.id, [])),
                )
            )

        route_stats = await self._analytics.route_stats(now)
        module_stats = await self._analytics.module_stats()
        hard_ids = hardest_modules(module_stats, limit=5)
        pims = await self._pims.summary()

        routes_summary = tuple(
            {
                "code": r.code,
                "title": r.title,
                "enrolled": r.enrolled,
                "completion_rate_pct": r.completion_rate,
                "pass_rate_pct": r.pass_rate,
                "stalled": r.stalled,
            }
            for r in route_stats
        )
        hard_modules = tuple(
            {
                "route": m.route_code,
                "slug": mod_slug.get(m.id),
                "order": m.order,
                "title": m.title,
                "attempts": m.attempts,
                "pass_rate_pct": m.pass_rate,
                "avg_score_pct": m.avg_score,
            }
            for m in module_stats
            if m.id in hard_ids
            or (m.pass_rate is not None and m.pass_rate < 75 and m.attempts >= 2)
        )
        pims_summary = {
            "total": pims.total,
            "in_force": pims.in_force,
            "by_state": pims.counts,
            "open_change_requests": pims.open_change_requests,
        }

        return AdminCohortSnapshot(
            learners=tuple(learners),
            routes_summary=routes_summary,
            hard_modules=hard_modules,
            pims_summary=pims_summary,
            valid_route_codes=frozenset(r.code for r in routes),
        )
