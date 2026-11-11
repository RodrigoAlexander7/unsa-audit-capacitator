from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from unsa_audit.documents.application.errors import (
    AlreadyResolved,
    ChangeRequestNotFound,
    DocumentNotFound,
    InvalidChangeRequest,
    NoChanges,
    StaleBase,
    VersionNotFound,
)
from unsa_audit.documents.application.ports import (
    ApplyOutcome,
    DocumentRepository,
    DocumentSource,
    DocumentSummary,
)
from unsa_audit.documents.domain.diff import Diff, compute_diff, content_hash, normalize_content
from unsa_audit.documents.domain.documents import (
    MAX_CONTENT_CHARS,
    MAX_NOTE_CHARS,
    MAX_RATIONALE_CHARS,
    MAX_TITLE_CHARS,
    ChangeImpact,
    ChangeRequest,
    ChangeStatus,
    Document,
    DocumentVersion,
)

Clock = Callable[[], datetime]


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Decision(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"


@dataclass(frozen=True)
class DocumentDetail:
    summary: DocumentSummary
    current: DocumentVersion


@dataclass(frozen=True)
class VersionDiff:
    document: Document
    from_number: int
    to_number: int
    diff: Diff


@dataclass(frozen=True)
class ChangeRequestDetail:
    change: ChangeRequest
    diff: Diff


# ----------------------------------------------------------------------------- lectura


class ListDocuments:
    def __init__(self, repo: DocumentRepository) -> None:
        self._repo = repo

    async def execute(self) -> list[DocumentSummary]:
        return await self._repo.list_summaries()


class GetDocument:
    def __init__(self, repo: DocumentRepository) -> None:
        self._repo = repo

    async def execute(self, code: str) -> DocumentDetail:
        summary = await self._repo.get_summary(code)
        if summary is None or summary.document.current_version_id is None:
            raise DocumentNotFound
        current = await self._repo.get_version_by_id(summary.document.current_version_id)
        if current is None:
            raise DocumentNotFound
        return DocumentDetail(summary, current)


async def _document(repo: DocumentRepository, code: str) -> Document:
    document = await repo.get_document(code)
    if document is None:
        raise DocumentNotFound
    return document


class ListVersions:
    def __init__(self, repo: DocumentRepository) -> None:
        self._repo = repo

    async def execute(self, code: str) -> tuple[Document, list[DocumentVersion]]:
        document = await _document(self._repo, code)
        versions = await self._repo.list_versions(document.id)
        return document, sorted(versions, key=lambda v: v.number)


class GetVersion:
    def __init__(self, repo: DocumentRepository) -> None:
        self._repo = repo

    async def execute(self, code: str, number: int) -> tuple[Document, DocumentVersion]:
        document = await _document(self._repo, code)
        version = await self._repo.get_version(document.id, number)
        if version is None:
            raise VersionNotFound
        return document, version


class GetDiff:
    def __init__(self, repo: DocumentRepository) -> None:
        self._repo = repo

    async def execute(
        self, code: str, to_number: int, from_number: int | None = None
    ) -> VersionDiff:
        document = await _document(self._repo, code)
        from_number = from_number if from_number is not None else to_number - 1
        old = await self._repo.get_version(document.id, from_number)
        new = await self._repo.get_version(document.id, to_number)
        if old is None or new is None:
            raise VersionNotFound
        return VersionDiff(
            document, from_number, to_number, compute_diff(old.content_md, new.content_md)
        )


# ----------------------------------------------------------------------------- solicitudes


class ProposeChange:
    def __init__(
        self,
        repo: DocumentRepository,
        clock: Clock = _utcnow,
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._repo = repo
        self._clock = clock
        self._id_factory = id_factory

    async def execute(
        self,
        user_id: UUID,
        user_name: str,
        code: str,
        title: str,
        rationale: str,
        impact: ChangeImpact,
        proposed_content_md: str,
    ) -> ChangeRequest:
        title, rationale = title.strip(), rationale.strip()
        if not title or not rationale or not proposed_content_md.strip():
            raise InvalidChangeRequest
        if (
            len(title) > MAX_TITLE_CHARS
            or len(rationale) > MAX_RATIONALE_CHARS
            or len(proposed_content_md) > MAX_CONTENT_CHARS
        ):
            raise InvalidChangeRequest

        summary = await self._repo.get_summary(code)
        if summary is None or summary.document.current_version_id is None:
            raise DocumentNotFound
        base = await self._repo.get_version_by_id(summary.document.current_version_id)
        if base is None:
            raise DocumentNotFound
        if content_hash(proposed_content_md) == base.content_hash:
            raise NoChanges

        change = ChangeRequest(
            id=self._id_factory(),
            document_id=summary.document.id,
            document_code=code,
            title=title,
            rationale=rationale,
            impact=impact,
            proposed_content_md=normalize_content(proposed_content_md),
            base_version_id=base.id,
            base_version_number=base.number,
            status=ChangeStatus.OPEN,
            proposed_by=user_id,
            proposed_by_name=user_name,
            created_at=self._clock(),
        )
        await self._repo.add_change_request(change)
        return change


class ListChangeRequests:
    def __init__(self, repo: DocumentRepository) -> None:
        self._repo = repo

    async def execute(
        self, status: ChangeStatus | None = None, code: str | None = None
    ) -> list[ChangeRequest]:
        if code is not None:
            await _document(self._repo, code)
        return await self._repo.list_change_requests(status, code)


class GetChangeRequest:
    def __init__(self, repo: DocumentRepository) -> None:
        self._repo = repo

    async def execute(self, change_id: UUID) -> ChangeRequestDetail:
        change = await self._repo.get_change_request(change_id)
        if change is None:
            raise ChangeRequestNotFound
        base = await self._repo.get_version_by_id(change.base_version_id)
        if base is None:
            raise VersionNotFound
        return ChangeRequestDetail(
            change, compute_diff(base.content_md, change.proposed_content_md)
        )


class ResolveChangeRequest:
    def __init__(
        self,
        repo: DocumentRepository,
        clock: Clock = _utcnow,
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._repo = repo
        self._clock = clock
        self._id_factory = id_factory

    async def execute(
        self, change_id: UUID, resolver_id: UUID, resolver_name: str, decision: Decision, note: str
    ) -> ChangeRequest:
        note = note.strip()
        if len(note) > MAX_NOTE_CHARS:
            raise InvalidChangeRequest
        change = await self._repo.get_change_request(change_id)
        if change is None:
            raise ChangeRequestNotFound
        if change.status is not ChangeStatus.OPEN:
            raise AlreadyResolved
        now = self._clock()

        if decision is Decision.REJECT:
            if not await self._repo.reject_change_request(
                change_id, resolver_id, resolver_name, note, now
            ):
                raise AlreadyResolved
        else:
            base = await self._repo.get_version_by_id(change.base_version_id)
            document = await self._repo.get_summary(change.document_code)
            if base is None or document is None:
                raise DocumentNotFound
            if document.document.current_version_id != change.base_version_id:
                raise StaleBase
            version = DocumentVersion(
                id=self._id_factory(),
                document_id=change.document_id,
                number=base.number + 1,
                content_md=normalize_content(change.proposed_content_md),
                content_hash=content_hash(change.proposed_content_md),
                parent_version_id=base.id,
                author_id=change.proposed_by,
                author_label=change.proposed_by_name,
                message=change.title,
                created_at=now,
            )
            outcome = await self._repo.apply_change(
                change_id, change.base_version_id, version, resolver_id, resolver_name, note, now
            )
            if outcome is ApplyOutcome.STALE:
                raise StaleBase
            if outcome is ApplyOutcome.NOT_OPEN:
                raise AlreadyResolved

        resolved = await self._repo.get_change_request(change_id)
        assert resolved is not None
        return resolved


# ----------------------------------------------------------------------------- contenido


class SyncDocuments:
    """Carga los documentos iniciales. Por defecto no pisa lo existente."""

    def __init__(self, repo: DocumentRepository, source: DocumentSource) -> None:
        self._repo = repo
        self._source = source

    async def execute(self, reset: bool = False) -> tuple[int, int]:
        """Devuelve (creados, omitidos)."""
        if reset:
            await self._repo.delete_all()
        created = skipped = 0
        for seed in self._source.load():
            if await self._repo.document_exists(seed.document.code):
                skipped += 1
                continue
            await self._repo.create_document(seed)
            created += 1
        return created, skipped
