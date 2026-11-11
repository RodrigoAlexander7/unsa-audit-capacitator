from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from unsa_audit.documents.domain.documents import (
    ChangeRequest,
    ChangeStatus,
    Document,
    DocumentVersion,
)
from unsa_audit.documents.domain.pims import PimsRequirement


@dataclass(frozen=True)
class DocumentSummary:
    document: Document
    owner_unit_name: str | None
    current_number: int
    updated_at: datetime
    open_change_requests: int


@dataclass(frozen=True)
class SeedDocument:
    document: Document
    versions: list[DocumentVersion]


class ApplyOutcome(StrEnum):
    APPLIED = "applied"
    STALE = "stale"
    NOT_OPEN = "not_open"


class DocumentSource(Protocol):
    def load(self) -> list[SeedDocument]: ...


@dataclass(frozen=True)
class PimsRequirementView:
    requirement: PimsRequirement
    responsible_unit_name: str | None


class PimsRequirementSource(Protocol):
    def load(self) -> list[PimsRequirement]: ...


class PimsRequirementRepository(Protocol):
    async def replace_all(self, requirements: list[PimsRequirement]) -> None:
        """Dato de referencia: reemplaza el conjunto completo (upsert + borra los retirados)."""
        ...

    async def list_all(self) -> list[PimsRequirementView]:
        """Ordenados por `sort_order`."""
        ...


class DocumentRepository(Protocol):
    # --- lectura
    async def list_summaries(self) -> list[DocumentSummary]: ...

    async def get_summary(self, code: str) -> DocumentSummary | None: ...

    async def get_document(self, code: str) -> Document | None: ...

    async def list_versions(self, document_id: UUID) -> list[DocumentVersion]: ...

    async def get_version(self, document_id: UUID, number: int) -> DocumentVersion | None: ...

    async def get_version_by_id(self, version_id: UUID) -> DocumentVersion | None: ...

    # --- solicitudes
    async def add_change_request(self, change: ChangeRequest) -> None: ...

    async def get_change_request(self, change_id: UUID) -> ChangeRequest | None: ...

    async def list_change_requests(
        self, status: ChangeStatus | None = None, document_code: str | None = None
    ) -> list[ChangeRequest]: ...

    async def reject_change_request(
        self, change_id: UUID, resolved_by: UUID, resolved_by_name: str, note: str, at: datetime
    ) -> bool:
        """Marca como rechazada si sigue abierta. False si ya estaba resuelta."""
        ...

    async def apply_change(
        self,
        change_id: UUID,
        expected_base_version_id: UUID,
        version: DocumentVersion,
        resolved_by: UUID,
        resolved_by_name: str,
        note: str,
        at: datetime,
    ) -> ApplyOutcome:
        """Atomico: crea la version, avanza la vigente y aprueba la solicitud (compare-and-set)."""
        ...

    # --- seed
    async def document_exists(self, code: str) -> bool: ...

    async def create_document(self, seed: SeedDocument) -> None: ...

    async def delete_all(self) -> None: ...
