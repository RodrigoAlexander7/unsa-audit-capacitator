import hashlib
import json
import time
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from unsa_audit.analytics.application.errors import (
    AdvisorUnavailable,
    InvalidQuestion,
    RouteStatsNotFound,
)
from unsa_audit.analytics.application.ports import (
    AdvisorQueryRepository,
    AnalyticsAdvisorPort,
    AnalyticsReadRepository,
    PimsSummaryProvider,
)
from unsa_audit.analytics.domain.stats import (
    AdvisorQuery,
    AssessmentProfileStats,
    ModuleStats,
    RouteStats,
    hardest_modules,
)

Clock = Callable[[], datetime]
MAX_QUESTION_CHARS = 1000


def _utcnow() -> datetime:
    return datetime.now(UTC)


class GetRouteStats:
    def __init__(self, repo: AnalyticsReadRepository, clock: Clock = _utcnow) -> None:
        self._repo = repo
        self._clock = clock

    async def execute(self) -> list[RouteStats]:
        return sorted(await self._repo.route_stats(self._clock()), key=lambda r: r.order)


@dataclass(frozen=True)
class RouteDetailStats:
    route: RouteStats
    modules: list[ModuleStats]


class GetRouteDetailStats:
    def __init__(self, repo: AnalyticsReadRepository, clock: Clock = _utcnow) -> None:
        self._repo = repo
        self._clock = clock

    async def execute(self, code: str) -> RouteDetailStats:
        route = next(
            (r for r in await self._repo.route_stats(self._clock()) if r.code == code), None
        )
        if route is None:
            raise RouteStatsNotFound
        modules = await self._repo.module_stats(code)
        hard = hardest_modules(modules)
        ordered = sorted(modules, key=lambda m: m.order)
        return RouteDetailStats(route, [replace(m, hardest=m.id in hard) for m in ordered])


class GetAssessmentStats:
    def __init__(self, repo: AnalyticsReadRepository) -> None:
        self._repo = repo

    async def execute(self) -> list[AssessmentProfileStats]:
        return await self._repo.assessment_stats()


# ----------------------------------------------------------------------------- snapshot e IA


@dataclass(frozen=True)
class Snapshot:
    data: dict[str, Any]
    hash: str


def _canonical(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class BuildSnapshot:
    """Agregado y anonimizado: no recibe ni expone identificadores de personas."""

    def __init__(
        self, repo: AnalyticsReadRepository, pims: PimsSummaryProvider, clock: Clock = _utcnow
    ) -> None:
        self._repo = repo
        self._pims = pims
        self._clock = clock

    async def execute(self) -> Snapshot:
        now = self._clock()
        routes = sorted(await self._repo.route_stats(now), key=lambda r: r.order)
        modules = await self._repo.module_stats(None)
        hard = hardest_modules(modules)
        participants = await self._repo.participants(now)
        assessments = await self._repo.assessment_stats()
        pims = await self._pims.summary()
        titles = {r.code: r.title for r in routes}

        body: dict[str, Any] = {
            "participants": {
                "total": participants.total,
                "new_last_7_days": participants.new_last_7_days,
            },
            "routes": [
                {
                    "code": r.code,
                    "title": r.title,
                    "planned_hours": r.hours,
                    "published_modules": r.modules_total,
                    "enrolled": r.enrolled,
                    "in_progress": r.in_progress,
                    "completed": r.completed,
                    "completion_rate_pct": r.completion_rate,
                    "avg_progress_pct": r.avg_progress,
                    "avg_hours_credited": r.avg_hours_credited,
                    "exercise_attempts": r.attempts,
                    "attempt_pass_rate_pct": r.pass_rate,
                    "stalled_last_7_days": r.stalled,
                }
                for r in routes
            ],
            "modules": [
                {
                    "route": titles.get(m.route_code, m.route_code),
                    "order": m.order,
                    "title": m.title,
                    "attempts": m.attempts,
                    "learners_completed": m.learners_completed,
                    "avg_score_pct": m.avg_score,
                    "pass_rate_pct": m.pass_rate,
                    "among_hardest": m.id in hard,
                }
                for m in sorted(modules, key=lambda m: (m.route_code, m.order))
            ],
            "assessments": [
                {
                    "profile": a.profile,
                    "finished": a.finished,
                    "avg_score_pct": a.avg_score,
                    "pass_rate_pct": a.pass_rate,
                    "competencies": [
                        {"name": g.label, "avg_correct_pct": g.average, "evaluations": g.samples}
                        for g in a.competencies
                    ],
                    "pims_requirements": [
                        {"name": g.label, "avg_correct_pct": g.average, "evaluations": g.samples}
                        for g in a.requirements
                    ],
                }
                for a in assessments
            ],
            "pims_documents": {
                "as_of": pims.as_of.isoformat(),
                "requirements_total": pims.total,
                "in_force": pims.in_force,
                "by_state": pims.counts,
                "requirements": [
                    {"clause": r.clause_ref, "title": r.title, "state": r.state}
                    for r in pims.requirements
                ],
                "open_change_requests": pims.open_change_requests,
            },
        }
        digest = hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()
        return Snapshot({"generated_at": now.isoformat(), **body}, digest)


def build_prompt(system_prompt: str, snapshot: dict[str, Any], question: str) -> str:
    """Prompt unico: reglas de sistema + DATOS (JSON) + PREGUNTA, cada bloque una sola vez."""
    data = json.dumps(snapshot, ensure_ascii=False, indent=1)
    return (
        f"{system_prompt.strip()}\n\n"
        f"DATOS (JSON agregado y anonimizado):\n{data}\n\n"
        f"PREGUNTA: {question.strip()}"
    )


class AskAdvisor:
    def __init__(
        self,
        snapshots: BuildSnapshot,
        advisor: AnalyticsAdvisorPort,
        queries: AdvisorQueryRepository,
        system_prompt: str,
        clock: Clock = _utcnow,
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._snapshots = snapshots
        self._advisor = advisor
        self._queries = queries
        self._system_prompt = system_prompt
        self._clock = clock
        self._id_factory = id_factory

    async def execute(self, user_id: UUID, question: str) -> AdvisorQuery:
        question = question.strip()
        if not question or len(question) > MAX_QUESTION_CHARS:
            raise InvalidQuestion
        snapshot = await self._snapshots.execute()
        prompt = build_prompt(self._system_prompt, snapshot.data, question)

        started = time.monotonic()
        try:
            answer = await self._advisor.ask(prompt)
        except AdvisorUnavailable as exc:
            await self._queries.add(
                AdvisorQuery(
                    id=self._id_factory(),
                    asked_by=user_id,
                    question=question,
                    snapshot_hash=snapshot.hash,
                    status="error",
                    answer=None,
                    error=str(exc) or type(exc).__name__,
                    duration_ms=int((time.monotonic() - started) * 1000),
                    created_at=self._clock(),
                )
            )
            raise
        query = AdvisorQuery(
            id=self._id_factory(),
            asked_by=user_id,
            question=question,
            snapshot_hash=snapshot.hash,
            status="ok",
            answer=answer.text,
            error=None,
            duration_ms=answer.duration_ms,
            created_at=self._clock(),
        )
        await self._queries.add(query)
        return query


class ListAdvisorHistory:
    def __init__(self, queries: AdvisorQueryRepository) -> None:
        self._queries = queries

    async def execute(self, limit: int = 50) -> list[AdvisorQuery]:
        return await self._queries.list_recent(limit)
