from dataclasses import replace
from datetime import datetime
from uuid import UUID

from unsa_audit.documents.application.ports import ApplyOutcome, DocumentSummary, SeedDocument
from unsa_audit.documents.domain.documents import (
    ChangeRequest,
    ChangeStatus,
    Document,
    DocumentVersion,
)


class InMemoryDocumentRepository:
    def __init__(self) -> None:
        self.documents: dict[UUID, Document] = {}
        self.versions: dict[UUID, DocumentVersion] = {}
        self.changes: dict[UUID, ChangeRequest] = {}

    def _summary(self, d: Document) -> DocumentSummary:
        current = self.versions[d.current_version_id]  # type: ignore[index]
        open_count = sum(
            1 for c in self.changes.values()
            if c.document_id == d.id and c.status is ChangeStatus.OPEN
        )  # fmt: skip
        return DocumentSummary(d, d.owner_unit_code, current.number, current.created_at, open_count)

    async def list_summaries(self) -> list[DocumentSummary]:
        return [self._summary(d) for d in sorted(self.documents.values(), key=lambda d: d.code)]

    async def get_summary(self, code: str) -> DocumentSummary | None:
        document = await self.get_document(code)
        return self._summary(document) if document else None

    async def get_document(self, code: str) -> Document | None:
        return next((d for d in self.documents.values() if d.code == code), None)

    async def list_versions(self, document_id: UUID) -> list[DocumentVersion]:
        return [v for v in self.versions.values() if v.document_id == document_id]

    async def get_version(self, document_id: UUID, number: int) -> DocumentVersion | None:
        return next(
            (
                v
                for v in self.versions.values()
                if v.document_id == document_id and v.number == number
            ),
            None,
        )

    async def get_version_by_id(self, version_id: UUID) -> DocumentVersion | None:
        return self.versions.get(version_id)

    async def add_change_request(self, change: ChangeRequest) -> None:
        self.changes[change.id] = change

    async def get_change_request(self, change_id: UUID) -> ChangeRequest | None:
        return self.changes.get(change_id)

    async def list_change_requests(
        self, status: ChangeStatus | None = None, document_code: str | None = None
    ) -> list[ChangeRequest]:
        return [
            c for c in self.changes.values()
            if (status is None or c.status is status)
            and (document_code is None or c.document_code == document_code)
        ]  # fmt: skip

    async def reject_change_request(
        self, change_id: UUID, resolved_by: UUID, resolved_by_name: str, note: str, at: datetime
    ) -> bool:
        change = self.changes[change_id]
        if change.status is not ChangeStatus.OPEN:
            return False
        self.changes[change_id] = replace(
            change, status=ChangeStatus.REJECTED, resolved_by=resolved_by,
            resolved_by_name=resolved_by_name, resolution_note=note, resolved_at=at,
        )  # fmt: skip
        return True

    async def apply_change(
        self, change_id, expected_base_version_id, version, resolved_by, resolved_by_name, note, at
    ) -> ApplyOutcome:
        change = self.changes[change_id]
        if change.status is not ChangeStatus.OPEN:
            return ApplyOutcome.NOT_OPEN
        document = self.documents[change.document_id]
        if document.current_version_id != expected_base_version_id:
            return ApplyOutcome.STALE
        self.versions[version.id] = version
        self.documents[document.id] = replace(document, current_version_id=version.id)
        self.changes[change_id] = replace(
            change, status=ChangeStatus.APPROVED, resolved_by=resolved_by,
            resolved_by_name=resolved_by_name, resolution_note=note, resolved_at=at,
            resulting_version_id=version.id, resulting_version_number=version.number,
        )  # fmt: skip
        return ApplyOutcome.APPLIED

    async def document_exists(self, code: str) -> bool:
        return await self.get_document(code) is not None

    async def create_document(self, seed: SeedDocument) -> None:
        self.documents[seed.document.id] = seed.document
        for v in seed.versions:
            self.versions[v.id] = v

    async def delete_all(self) -> None:
        self.documents.clear()
        self.versions.clear()
        self.changes.clear()
