from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Protocol

from unsa_audit.analytics.domain.stats import (
    AdvisorQuery,
    AssessmentProfileStats,
    ModuleStats,
    ParticipantCounts,
    RouteStats,
)


class AnalyticsReadRepository(Protocol):
    async def route_stats(self, now: datetime) -> list[RouteStats]: ...

    async def module_stats(self, route_code: str | None = None) -> list[ModuleStats]: ...

    async def assessment_stats(self) -> list[AssessmentProfileStats]: ...

    async def participants(self, now: datetime) -> ParticipantCounts: ...


@dataclass(frozen=True)
class AdvisorAnswer:
    text: str
    duration_ms: int


class AnalyticsAdvisorPort(Protocol):
    async def ask(self, prompt: str) -> AdvisorAnswer:
        """Lanza AdvisorTimeout o AdvisorUnavailable si no puede responder."""
        ...


class AdvisorQueryRepository(Protocol):
    async def add(self, query: AdvisorQuery) -> None: ...

    async def list_recent(self, limit: int) -> list[AdvisorQuery]: ...


@dataclass(frozen=True)
class PimsRequirementState:
    clause_ref: str
    title: str
    state: str


@dataclass(frozen=True)
class PimsSummary:
    as_of: date
    total: int
    in_force: int
    counts: dict[str, int]
    requirements: list[PimsRequirementState] = field(default_factory=list)
    open_change_requests: int = 0


class PimsSummaryProvider(Protocol):
    async def summary(self) -> PimsSummary: ...
