"""Repositorio SQLAlchemy para propuestas de reestructuracion curricular."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from unsa_audit.assistant.domain.admin_cohort import CurriculumProposal
from unsa_audit.assistant.infrastructure.models import CurriculumProposalModel


def _to_domain(row: CurriculumProposalModel) -> CurriculumProposal:
    return CurriculumProposal(
        id=row.id,
        created_by=row.created_by,
        title=row.title,
        target_route_code=row.target_route_code,
        target_module_slug=row.target_module_slug,
        change_type=row.change_type,
        proposed_change=row.proposed_change,
        rationale=row.rationale,
        evidence_metrics=dict(row.evidence_metrics or {}),
        status=row.status,
        review_note=row.review_note,
        context_hash=row.context_hash,
        created_at=row.created_at,
        reviewed_at=row.reviewed_at,
    )


class SqlAlchemyCurriculumProposalRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    async def add_many(self, proposals: list[CurriculumProposal]) -> None:
        async with self._sf() as session, session.begin():
            for prop in proposals:
                session.add(
                    CurriculumProposalModel(
                        id=prop.id,
                        created_by=prop.created_by,
                        title=prop.title,
                        target_route_code=prop.target_route_code,
                        target_module_slug=prop.target_module_slug,
                        change_type=prop.change_type,
                        proposed_change=prop.proposed_change,
                        rationale=prop.rationale,
                        evidence_metrics=prop.evidence_metrics,
                        status=prop.status,
                        review_note=prop.review_note,
                        context_hash=prop.context_hash,
                        created_at=prop.created_at,
                        reviewed_at=prop.reviewed_at,
                    )
                )

    async def list_recent(self, limit: int = 30) -> list[CurriculumProposal]:
        async with self._sf() as session:
            rows = await session.scalars(
                select(CurriculumProposalModel)
                .order_by(CurriculumProposalModel.created_at.desc())
                .limit(limit)
            )
            return [_to_domain(row) for row in rows]

    async def get(self, proposal_id: UUID) -> CurriculumProposal | None:
        async with self._sf() as session:
            row = await session.get(CurriculumProposalModel, proposal_id)
            return _to_domain(row) if row is not None else None

    async def update_status(self, proposal: CurriculumProposal) -> CurriculumProposal:
        async with self._sf() as session, session.begin():
            row = await session.get(CurriculumProposalModel, proposal.id)
            assert row is not None
            row.status = proposal.status
            row.review_note = proposal.review_note
            row.reviewed_at = proposal.reviewed_at
            return _to_domain(row)
