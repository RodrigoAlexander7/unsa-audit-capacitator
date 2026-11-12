"""Puertos de aplicacion para el modo administrador y propuestas."""

from typing import Protocol
from uuid import UUID

from unsa_audit.assistant.domain.admin_cohort import (
    AdminCohortSnapshot,
    CurriculumProposal,
)


class AdminCohortProvider(Protocol):
    async def snapshot(self) -> AdminCohortSnapshot: ...


class CurriculumProposalRepository(Protocol):
    async def add_many(self, proposals: list[CurriculumProposal]) -> None: ...

    async def list_recent(self, limit: int = 30) -> list[CurriculumProposal]: ...

    async def get(self, proposal_id: UUID) -> CurriculumProposal | None: ...

    async def update_status(self, proposal: CurriculumProposal) -> CurriculumProposal: ...
