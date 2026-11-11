from dataclasses import replace

from unsa_audit.documents.application.pims_use_cases import GetPimsCompleteness
from unsa_audit.learning.application.ports import PimsFact, UniversityFacts, UniversitySnapshot


class LearningFacts:
    """Compone los hechos de la universidad con el estado real del conjunto PIMS.

    `learning` no conoce las tablas de `documents`: usa su caso de uso de completitud.
    """

    def __init__(self, university: UniversityFacts, pims: GetPimsCompleteness) -> None:
        self._university = university
        self._pims = pims

    async def snapshot(self) -> UniversitySnapshot:
        base = await self._university.snapshot()
        completeness = await self._pims.execute()
        facts = []
        for item in completeness.items:
            summary = item.document
            facts.append(
                PimsFact(
                    code=item.requirement.requirement.code,
                    clause_ref=item.requirement.requirement.clause_ref,
                    title=item.requirement.requirement.title,
                    state=item.evaluation.state.value,
                    document_title=summary.document.title if summary else None,
                    version=summary.current_number if summary else None,
                    review_date=summary.document.review_date if summary else None,
                    owner_unit_name=summary.owner_unit_name if summary else None,
                )
            )
        return replace(base, pims=facts)
