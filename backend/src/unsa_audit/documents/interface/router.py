from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from unsa_audit.documents.application.errors import (
    AlreadyResolved,
    ChangeRequestNotFound,
    DocumentNotFound,
    InvalidChangeRequest,
    NoChanges,
    StaleBase,
    VersionNotFound,
)
from unsa_audit.documents.application.ports import DocumentSummary
from unsa_audit.documents.application.use_cases import ChangeRequestDetail, Decision, DocumentDetail
from unsa_audit.documents.domain.diff import Diff
from unsa_audit.documents.domain.documents import (
    MAX_CONTENT_CHARS,
    MAX_NOTE_CHARS,
    MAX_RATIONALE_CHARS,
    MAX_TITLE_CHARS,
    ChangeImpact,
    ChangeRequest,
    ChangeStatus,
    DocumentVersion,
)
from unsa_audit.identity.interface.dependencies import CurrentUser, SuperAdmin

router = APIRouter(tags=["documents"])


# ----------------------------------------------------------------------------- schemas


class DocumentSummaryResponse(BaseModel):
    code: str
    kind: str
    title: str
    owner_unit_code: str | None
    owner_unit_name: str | None
    lifecycle: str
    review_date: date | None
    current_version: int
    updated_at: datetime
    open_change_requests: int

    @classmethod
    def from_domain(cls, s: DocumentSummary) -> "DocumentSummaryResponse":
        d = s.document
        return cls(
            code=d.code,
            kind=d.kind.value,
            title=d.title,
            owner_unit_code=d.owner_unit_code,
            owner_unit_name=s.owner_unit_name,
            lifecycle=d.lifecycle.value,
            review_date=d.review_date,
            current_version=s.current_number,
            updated_at=s.updated_at,
            open_change_requests=s.open_change_requests,
        )


class DocumentDetailResponse(DocumentSummaryResponse):
    content_md: str
    content_hash: str
    author_label: str
    message: str

    @classmethod
    def from_detail(cls, detail: DocumentDetail) -> "DocumentDetailResponse":
        base = DocumentSummaryResponse.from_domain(detail.summary)
        return cls(
            **base.model_dump(),
            content_md=detail.current.content_md,
            content_hash=detail.current.content_hash,
            author_label=detail.current.author_label,
            message=detail.current.message,
        )


class VersionResponse(BaseModel):
    number: int
    message: str
    author_label: str
    created_at: datetime
    content_hash: str
    parent_number: int | None

    @classmethod
    def from_domain(cls, v: DocumentVersion) -> "VersionResponse":
        return cls(
            number=v.number,
            message=v.message,
            author_label=v.author_label,
            created_at=v.created_at,
            content_hash=v.content_hash,
            parent_number=v.number - 1 if v.parent_version_id else None,
        )


class VersionDetailResponse(VersionResponse):
    document_code: str
    content_md: str


class DiffLineResponse(BaseModel):
    kind: Literal["add", "del", "ctx"]
    old_line: int | None
    new_line: int | None
    text: str


class HunkResponse(BaseModel):
    old_start: int
    new_start: int
    lines: list[DiffLineResponse]


class DiffResponse(BaseModel):
    additions: int
    deletions: int
    hunks: list[HunkResponse]

    @classmethod
    def from_domain(cls, diff: Diff) -> "DiffResponse":
        return cls(
            additions=diff.additions,
            deletions=diff.deletions,
            hunks=[
                HunkResponse(
                    old_start=h.old_start,
                    new_start=h.new_start,
                    lines=[
                        DiffLineResponse(kind=line.kind, old_line=line.old_line,
                                         new_line=line.new_line, text=line.text)
                        for line in h.lines
                    ],
                )
                for h in diff.hunks
            ],
        )  # fmt: skip


class VersionDiffResponse(DiffResponse):
    document_code: str
    from_version: int
    to_version: int


class ChangeRequestResponse(BaseModel):
    id: str
    document_code: str
    title: str
    rationale: str
    impact: str
    status: str
    base_version: int
    proposed_by_name: str
    created_at: datetime
    resolved_by_name: str | None
    resolution_note: str | None
    resulting_version: int | None
    resolved_at: datetime | None

    @classmethod
    def from_domain(cls, c: ChangeRequest) -> "ChangeRequestResponse":
        return cls(
            id=str(c.id),
            document_code=c.document_code,
            title=c.title,
            rationale=c.rationale,
            impact=c.impact.value,
            status=c.status.value,
            base_version=c.base_version_number,
            proposed_by_name=c.proposed_by_name,
            created_at=c.created_at,
            resolved_by_name=c.resolved_by_name,
            resolution_note=c.resolution_note,
            resulting_version=c.resulting_version_number,
            resolved_at=c.resolved_at,
        )


class ChangeRequestDetailResponse(ChangeRequestResponse):
    proposed_content_md: str
    diff: DiffResponse

    @classmethod
    def from_detail(cls, d: ChangeRequestDetail) -> "ChangeRequestDetailResponse":
        base = ChangeRequestResponse.from_domain(d.change)
        return cls(
            **base.model_dump(),
            proposed_content_md=d.change.proposed_content_md,
            diff=DiffResponse.from_domain(d.diff),
        )


class ProposeRequest(BaseModel):
    title: str = Field(max_length=MAX_TITLE_CHARS)
    rationale: str = Field(max_length=MAX_RATIONALE_CHARS)
    impact: ChangeImpact
    proposed_content_md: str = Field(max_length=MAX_CONTENT_CHARS)


class ResolveRequest(BaseModel):
    decision: Literal["approve", "reject"]
    note: str = Field(default="", max_length=MAX_NOTE_CHARS)


# ----------------------------------------------------------------------------- lectura


def _not_found(message: str) -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, message)


@router.get("/documents", response_model=list[DocumentSummaryResponse])
async def list_documents(_: CurrentUser, request: Request) -> list[DocumentSummaryResponse]:
    summaries = await request.app.state.list_documents.execute()
    return [DocumentSummaryResponse.from_domain(s) for s in summaries]


@router.get("/documents/{code}", response_model=DocumentDetailResponse)
async def get_document(code: str, _: CurrentUser, request: Request) -> DocumentDetailResponse:
    try:
        detail = await request.app.state.get_document.execute(code)
    except DocumentNotFound as exc:
        raise _not_found("Documento no encontrado") from exc
    return DocumentDetailResponse.from_detail(detail)


@router.get("/documents/{code}/versions", response_model=list[VersionResponse])
async def list_versions(code: str, _: CurrentUser, request: Request) -> list[VersionResponse]:
    try:
        _doc, versions = await request.app.state.list_versions.execute(code)
    except DocumentNotFound as exc:
        raise _not_found("Documento no encontrado") from exc
    return [VersionResponse.from_domain(v) for v in versions]


@router.get("/documents/{code}/versions/{number}", response_model=VersionDetailResponse)
async def get_version(
    code: str, number: int, _: CurrentUser, request: Request
) -> VersionDetailResponse:
    try:
        document, version = await request.app.state.get_version.execute(code, number)
    except DocumentNotFound as exc:
        raise _not_found("Documento no encontrado") from exc
    except VersionNotFound as exc:
        raise _not_found("Versión no encontrada") from exc
    return VersionDetailResponse(
        **VersionResponse.from_domain(version).model_dump(),
        document_code=document.code,
        content_md=version.content_md,
    )


@router.get("/documents/{code}/diff", response_model=VersionDiffResponse)
async def get_diff(
    code: str,
    to: Annotated[int, Query(ge=1)],
    _: CurrentUser,
    request: Request,
    from_version: Annotated[int | None, Query(alias="from", ge=1)] = None,
) -> VersionDiffResponse:
    try:
        result = await request.app.state.get_diff.execute(code, to, from_version)
    except DocumentNotFound as exc:
        raise _not_found("Documento no encontrado") from exc
    except VersionNotFound as exc:
        raise _not_found("Versión no encontrada") from exc
    return VersionDiffResponse(
        **DiffResponse.from_domain(result.diff).model_dump(),
        document_code=result.document.code,
        from_version=result.from_number,
        to_version=result.to_number,
    )


# ----------------------------------------------------------------------------- solicitudes


@router.get("/documents/{code}/change-requests", response_model=list[ChangeRequestResponse])
async def list_document_change_requests(
    code: str,
    _: CurrentUser,
    request: Request,
    status_filter: Annotated[ChangeStatus | None, Query(alias="status")] = None,
) -> list[ChangeRequestResponse]:
    try:
        changes = await request.app.state.list_change_requests.execute(status_filter, code)
    except DocumentNotFound as exc:
        raise _not_found("Documento no encontrado") from exc
    return [ChangeRequestResponse.from_domain(c) for c in changes]


@router.post(
    "/documents/{code}/change-requests",
    response_model=ChangeRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def propose_change(
    code: str, body: ProposeRequest, user: CurrentUser, request: Request
) -> ChangeRequestResponse:
    try:
        change = await request.app.state.propose_change.execute(
            user.id, user.full_name, code, body.title, body.rationale, body.impact,
            body.proposed_content_md,
        )  # fmt: skip
    except DocumentNotFound as exc:
        raise _not_found("Documento no encontrado") from exc
    except InvalidChangeRequest as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "Completa el título, la justificación y el texto"
        ) from exc
    except NoChanges as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "El texto propuesto no cambia el documento vigente",
        ) from exc
    return ChangeRequestResponse.from_domain(change)


@router.get("/change-requests", response_model=list[ChangeRequestResponse])
async def list_change_requests(
    _: CurrentUser,
    request: Request,
    status_filter: Annotated[ChangeStatus | None, Query(alias="status")] = None,
) -> list[ChangeRequestResponse]:
    changes = await request.app.state.list_change_requests.execute(status_filter, None)
    return [ChangeRequestResponse.from_domain(c) for c in changes]


@router.get("/change-requests/{request_id}", response_model=ChangeRequestDetailResponse)
async def get_change_request(
    request_id: UUID, _: CurrentUser, request: Request
) -> ChangeRequestDetailResponse:
    try:
        detail = await request.app.state.get_change_request.execute(request_id)
    except (ChangeRequestNotFound, VersionNotFound) as exc:
        raise _not_found("Solicitud no encontrada") from exc
    return ChangeRequestDetailResponse.from_detail(detail)


@router.post("/change-requests/{request_id}/resolve", response_model=ChangeRequestResponse)
async def resolve_change_request(
    request_id: UUID, body: ResolveRequest, admin: SuperAdmin, request: Request
) -> ChangeRequestResponse:
    try:
        change = await request.app.state.resolve_change_request.execute(
            request_id, admin.id, admin.full_name, Decision(body.decision), body.note
        )
    except ChangeRequestNotFound as exc:
        raise _not_found("Solicitud no encontrada") from exc
    except AlreadyResolved as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {"code": "already_resolved", "message": "La solicitud ya fue resuelta."},
        ) from exc
    except StaleBase as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {
                "code": "stale_base",
                "message": "El documento cambió tras la propuesta: recházala y vuelve a proponer.",
            },
        ) from exc
    except InvalidChangeRequest as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Nota demasiado larga") from exc
    return ChangeRequestResponse.from_domain(change)
