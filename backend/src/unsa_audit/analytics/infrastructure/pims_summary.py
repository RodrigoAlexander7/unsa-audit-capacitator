from unsa_audit.analytics.application.ports import PimsRequirementState, PimsSummary
from unsa_audit.documents.application.pims_use_cases import GetPimsCompleteness
from unsa_audit.documents.application.ports import DocumentRepository
from unsa_audit.documents.domain.documents import ChangeStatus


class PimsSummaryAdapter:
    """Resume el estado del PIMS y las solicitudes de cambio abiertas (modulo documents)."""

    def __init__(self, completeness: GetPimsCompleteness, documents: DocumentRepository) -> None:
        self._completeness = completeness
        self._documents = documents

    async def summary(self) -> PimsSummary:
        c = await self._completeness.execute()
        open_changes = await self._documents.list_change_requests(ChangeStatus.OPEN)
        return PimsSummary(
            as_of=c.as_of,
            total=c.total,
            in_force=c.in_force,
            counts={state.value: n for state, n in c.counts.items()},
            requirements=[
                PimsRequirementState(
                    i.requirement.requirement.clause_ref,
                    i.requirement.requirement.title,
                    i.evaluation.state.value,
                )
                for i in c.items
            ],
            open_change_requests=len(open_changes),
        )
