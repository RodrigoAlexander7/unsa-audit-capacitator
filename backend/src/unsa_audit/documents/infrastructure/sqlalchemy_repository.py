from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from unsa_audit.documents.application.ports import (
    ApplyOutcome,
    DocumentSummary,
    PimsRequirementView,
    SeedDocument,
)
from unsa_audit.documents.domain.documents import (
    ChangeImpact,
    ChangeRequest,
    ChangeStatus,
    Document,
    DocumentKind,
    DocumentLifecycle,
    DocumentVersion,
)
from unsa_audit.documents.domain.pims import PimsRequirement
from unsa_audit.documents.infrastructure.models import (
    ChangeRequestModel,
    DocumentModel,
    DocumentVersionModel,
    PimsRequirementModel,
)
from unsa_audit.university.infrastructure.models import OrgUnitModel


class _StaleBase(Exception):
    pass


class _NotOpen(Exception):
    pass


def _document(m: DocumentModel) -> Document:
    return Document(
        m.id,
        m.code,
        DocumentKind(m.kind),
        m.title,
        m.owner_unit_code,
        m.current_version_id,
        DocumentLifecycle(m.lifecycle),
        m.review_date,
    )


def _version(m: DocumentVersionModel) -> DocumentVersion:
    return DocumentVersion(
        id=m.id,
        document_id=m.document_id,
        number=m.number,
        content_md=m.content_md,
        content_hash=m.content_hash,
        parent_version_id=m.parent_version_id,
        author_id=m.author_id,
        author_label=m.author_label,
        message=m.message,
        created_at=m.created_at,
    )


def _change(m: ChangeRequestModel) -> ChangeRequest:
    return ChangeRequest(
        id=m.id,
        document_id=m.document_id,
        document_code=m.document_code,
        title=m.title,
        rationale=m.rationale,
        impact=ChangeImpact(m.impact),
        proposed_content_md=m.proposed_content_md,
        base_version_id=m.base_version_id,
        base_version_number=m.base_version_number,
        status=ChangeStatus(m.status),
        proposed_by=m.proposed_by,
        proposed_by_name=m.proposed_by_name,
        created_at=m.created_at,
        resolved_by=m.resolved_by,
        resolved_by_name=m.resolved_by_name,
        resolution_note=m.resolution_note,
        resulting_version_id=m.resulting_version_id,
        resulting_version_number=m.resulting_version_number,
        resolved_at=m.resolved_at,
    )


def _version_model(v: DocumentVersion) -> DocumentVersionModel:
    return DocumentVersionModel(
        id=v.id,
        document_id=v.document_id,
        number=v.number,
        content_md=v.content_md,
        content_hash=v.content_hash,
        parent_version_id=v.parent_version_id,
        author_id=v.author_id,
        author_label=v.author_label,
        message=v.message,
        created_at=v.created_at,
    )


class SqlAlchemyDocumentRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    # ------------------------------------------------------------------ lectura

    async def _summaries(self, session: AsyncSession, code: str | None) -> list[DocumentSummary]:
        query = select(DocumentModel).order_by(DocumentModel.code)
        if code is not None:
            query = query.where(DocumentModel.code == code)
        documents = (await session.scalars(query)).all()
        if not documents:
            return []

        units = {u.code: u.name for u in await session.scalars(select(OrgUnitModel))}
        versions = {
            v.id: v
            for v in await session.scalars(
                select(DocumentVersionModel).where(
                    DocumentVersionModel.id.in_(
                        [d.current_version_id for d in documents if d.current_version_id]
                    )
                )
            )
        }
        counted = await session.execute(
            select(ChangeRequestModel.document_id, func.count())
            .where(ChangeRequestModel.status == ChangeStatus.OPEN.value)
            .group_by(ChangeRequestModel.document_id)
        )
        open_counts = {document_id: count for document_id, count in counted}
        result: list[DocumentSummary] = []
        for d in documents:
            current = versions.get(d.current_version_id) if d.current_version_id else None
            if current is None:
                continue
            result.append(
                DocumentSummary(
                    document=_document(d),
                    owner_unit_name=units.get(d.owner_unit_code or ""),
                    current_number=current.number,
                    updated_at=current.created_at,
                    open_change_requests=open_counts.get(d.id, 0),
                )
            )
        return result

    async def list_summaries(self) -> list[DocumentSummary]:
        async with self._sf() as session:
            return await self._summaries(session, None)

    async def get_summary(self, code: str) -> DocumentSummary | None:
        async with self._sf() as session:
            found = await self._summaries(session, code)
            return found[0] if found else None

    async def get_document(self, code: str) -> Document | None:
        async with self._sf() as session:
            row = await session.scalar(select(DocumentModel).where(DocumentModel.code == code))
            return _document(row) if row else None

    async def list_versions(self, document_id: UUID) -> list[DocumentVersion]:
        async with self._sf() as session:
            rows = await session.scalars(
                select(DocumentVersionModel)
                .where(DocumentVersionModel.document_id == document_id)
                .order_by(DocumentVersionModel.number)
            )
            return [_version(r) for r in rows]

    async def get_version(self, document_id: UUID, number: int) -> DocumentVersion | None:
        async with self._sf() as session:
            row = await session.scalar(
                select(DocumentVersionModel).where(
                    DocumentVersionModel.document_id == document_id,
                    DocumentVersionModel.number == number,
                )
            )
            return _version(row) if row else None

    async def get_version_by_id(self, version_id: UUID) -> DocumentVersion | None:
        async with self._sf() as session:
            row = await session.get(DocumentVersionModel, version_id)
            return _version(row) if row else None

    # ------------------------------------------------------------------ solicitudes

    async def add_change_request(self, change: ChangeRequest) -> None:
        async with self._sf() as session, session.begin():
            session.add(
                ChangeRequestModel(
                    id=change.id,
                    document_id=change.document_id,
                    document_code=change.document_code,
                    title=change.title,
                    rationale=change.rationale,
                    impact=change.impact.value,
                    proposed_content_md=change.proposed_content_md,
                    base_version_id=change.base_version_id,
                    base_version_number=change.base_version_number,
                    status=change.status.value,
                    proposed_by=change.proposed_by,
                    proposed_by_name=change.proposed_by_name,
                    created_at=change.created_at,
                )
            )

    async def get_change_request(self, change_id: UUID) -> ChangeRequest | None:
        async with self._sf() as session:
            row = await session.get(ChangeRequestModel, change_id)
            return _change(row) if row else None

    async def list_change_requests(
        self, status: ChangeStatus | None = None, document_code: str | None = None
    ) -> list[ChangeRequest]:
        async with self._sf() as session:
            query = select(ChangeRequestModel).order_by(ChangeRequestModel.created_at.desc())
            if status is not None:
                query = query.where(ChangeRequestModel.status == status.value)
            if document_code is not None:
                query = query.where(ChangeRequestModel.document_code == document_code)
            return [_change(r) for r in await session.scalars(query)]

    async def reject_change_request(
        self, change_id: UUID, resolved_by: UUID, resolved_by_name: str, note: str, at: datetime
    ) -> bool:
        async with self._sf() as session, session.begin():
            row = await session.get(ChangeRequestModel, change_id, with_for_update=True)
            if row is None or row.status != ChangeStatus.OPEN.value:
                return False
            row.status = ChangeStatus.REJECTED.value
            row.resolved_by = resolved_by
            row.resolved_by_name = resolved_by_name
            row.resolution_note = note
            row.resolved_at = at
            return True

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
        try:
            async with self._sf() as session, session.begin():
                change = await session.get(ChangeRequestModel, change_id, with_for_update=True)
                if change is None or change.status != ChangeStatus.OPEN.value:
                    raise _NotOpen
                document = await session.get(
                    DocumentModel, change.document_id, with_for_update=True
                )
                if document is None or document.current_version_id != expected_base_version_id:
                    raise _StaleBase

                session.add(_version_model(version))
                await session.flush()
                document.current_version_id = version.id
                change.status = ChangeStatus.APPROVED.value
                change.resolved_by = resolved_by
                change.resolved_by_name = resolved_by_name
                change.resolution_note = note
                change.resolved_at = at
                change.resulting_version_id = version.id
                change.resulting_version_number = version.number
        except _StaleBase:
            return ApplyOutcome.STALE
        except _NotOpen:
            return ApplyOutcome.NOT_OPEN
        return ApplyOutcome.APPLIED

    # ------------------------------------------------------------------ seed

    async def document_exists(self, code: str) -> bool:
        async with self._sf() as session:
            return (
                await session.scalar(select(DocumentModel.id).where(DocumentModel.code == code))
                is not None
            )

    async def create_document(self, seed: SeedDocument) -> None:
        d = seed.document
        async with self._sf() as session, session.begin():
            session.add(
                DocumentModel(
                    id=d.id,
                    code=d.code,
                    kind=d.kind.value,
                    title=d.title,
                    owner_unit_code=d.owner_unit_code,
                    lifecycle=d.lifecycle.value,
                    review_date=d.review_date,
                )
            )
            await session.flush()
            for version in sorted(seed.versions, key=lambda v: v.number):
                session.add(_version_model(version))
                await session.flush()
            row = await session.get(DocumentModel, d.id)
            assert row is not None
            row.current_version_id = max(seed.versions, key=lambda v: v.number).id

    async def delete_all(self) -> None:
        async with self._sf() as session, session.begin():
            await session.execute(delete(ChangeRequestModel))
            await session.execute(delete(DocumentModel))


class SqlAlchemyPimsRequirementRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    async def replace_all(self, requirements: list[PimsRequirement]) -> None:
        async with self._sf() as session, session.begin():
            # sort_order y document_kind son unicos: se vacia antes de reinsertar.
            await session.execute(delete(PimsRequirementModel))
            session.add_all(
                PimsRequirementModel(
                    id=r.id,
                    code=r.code,
                    clause_ref=r.clause_ref,
                    title=r.title,
                    document_kind=r.document_kind.value,
                    summary=r.summary,
                    expected_evidence=r.expected_evidence,
                    responsible_unit_code=r.responsible_unit_code,
                    sort_order=r.sort_order,
                )
                for r in requirements
            )

    async def list_all(self) -> list[PimsRequirementView]:
        async with self._sf() as session:
            units = {u.code: u.name for u in await session.scalars(select(OrgUnitModel))}
            rows = await session.scalars(
                select(PimsRequirementModel).order_by(PimsRequirementModel.sort_order)
            )
            return [
                PimsRequirementView(
                    PimsRequirement(
                        id=m.id,
                        code=m.code,
                        clause_ref=m.clause_ref,
                        title=m.title,
                        document_kind=DocumentKind(m.document_kind),
                        summary=m.summary,
                        expected_evidence=m.expected_evidence,
                        responsible_unit_code=m.responsible_unit_code,
                        sort_order=m.sort_order,
                    ),
                    units.get(m.responsible_unit_code or ""),
                )
                for m in rows
            ]
