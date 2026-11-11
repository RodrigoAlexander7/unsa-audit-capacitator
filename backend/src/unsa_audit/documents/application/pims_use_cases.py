from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from unsa_audit.documents.application.ports import (
    DocumentRepository,
    DocumentSummary,
    PimsRequirementRepository,
    PimsRequirementSource,
    PimsRequirementView,
)
from unsa_audit.documents.domain.pims import (
    RequirementState,
    StateEvaluation,
    evaluate_state,
    percent,
)

Today = Callable[[], date]


def _today() -> date:
    return date.today()


@dataclass(frozen=True)
class PimsItem:
    requirement: PimsRequirementView
    evaluation: StateEvaluation
    document: DocumentSummary | None


@dataclass(frozen=True)
class PimsCompleteness:
    items: list[PimsItem]
    counts: dict[RequirementState, int]
    total: int
    in_force: int
    percent_in_force: int
    as_of: date


class ListPimsRequirements:
    def __init__(self, requirements: PimsRequirementRepository) -> None:
        self._requirements = requirements

    async def execute(self) -> list[PimsRequirementView]:
        return await self._requirements.list_all()


class GetPimsCompleteness:
    def __init__(
        self,
        requirements: PimsRequirementRepository,
        documents: DocumentRepository,
        today: Today = _today,
    ) -> None:
        self._requirements = requirements
        self._documents = documents
        self._today = today

    async def execute(self) -> PimsCompleteness:
        today = self._today()
        by_kind = {s.document.kind: s for s in await self._documents.list_summaries()}
        items: list[PimsItem] = []
        for view in await self._requirements.list_all():
            summary = by_kind.get(view.requirement.document_kind)
            evaluation = evaluate_state(
                exists=summary is not None,
                lifecycle=summary.document.lifecycle if summary else None,
                review_date=summary.document.review_date if summary else None,
                owner_unit_code=summary.document.owner_unit_code if summary else None,
                today=today,
            )
            items.append(PimsItem(view, evaluation, summary))

        counts = {state: 0 for state in RequirementState}
        for item in items:
            counts[item.evaluation.state] += 1
        in_force = counts[RequirementState.IN_FORCE]
        return PimsCompleteness(
            items, counts, len(items), in_force, percent(in_force, len(items)), today
        )


class SyncPimsRequirements:
    def __init__(
        self, requirements: PimsRequirementRepository, source: PimsRequirementSource
    ) -> None:
        self._requirements = requirements
        self._source = source

    async def execute(self) -> int:
        loaded = self._source.load()
        await self._requirements.replace_all(loaded)
        return len(loaded)
