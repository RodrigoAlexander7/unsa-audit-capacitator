from datetime import date

from fastapi import APIRouter, Request
from pydantic import BaseModel

from unsa_audit.documents.application.pims_use_cases import PimsCompleteness, PimsItem
from unsa_audit.documents.application.ports import PimsRequirementView
from unsa_audit.identity.interface.dependencies import CurrentUser

router = APIRouter(prefix="/pims", tags=["pims"])


class RequirementResponse(BaseModel):
    code: str
    order: int
    clause_ref: str
    title: str
    document_kind: str
    summary: str
    expected_evidence: str
    responsible_unit_code: str | None
    responsible_unit_name: str | None

    @classmethod
    def from_view(cls, view: PimsRequirementView) -> "RequirementResponse":
        r = view.requirement
        return cls(
            code=r.code,
            order=r.sort_order,
            clause_ref=r.clause_ref,
            title=r.title,
            document_kind=r.document_kind.value,
            summary=r.summary,
            expected_evidence=r.expected_evidence,
            responsible_unit_code=r.responsible_unit_code,
            responsible_unit_name=view.responsible_unit_name,
        )


class PimsDocumentResponse(BaseModel):
    code: str
    title: str
    current_version: int
    lifecycle: str
    review_date: date | None
    owner_unit_code: str | None
    owner_unit_name: str | None


class CompletenessItemResponse(RequirementResponse):
    state: str
    issues: list[str]
    document: PimsDocumentResponse | None

    @classmethod
    def from_item(cls, item: PimsItem) -> "CompletenessItemResponse":
        base = RequirementResponse.from_view(item.requirement)
        summary = item.document
        document = None
        if summary is not None:
            d = summary.document
            document = PimsDocumentResponse(
                code=d.code,
                title=d.title,
                current_version=summary.current_number,
                lifecycle=d.lifecycle.value,
                review_date=d.review_date,
                owner_unit_code=d.owner_unit_code,
                owner_unit_name=summary.owner_unit_name,
            )
        return cls(
            **base.model_dump(),
            state=item.evaluation.state.value,
            issues=[i.value for i in item.evaluation.issues],
            document=document,
        )


class CompletenessResponse(BaseModel):
    as_of: date
    total: int
    in_force: int
    percent_in_force: int
    counts: dict[str, int]
    items: list[CompletenessItemResponse]

    @classmethod
    def from_domain(cls, c: PimsCompleteness) -> "CompletenessResponse":
        return cls(
            as_of=c.as_of,
            total=c.total,
            in_force=c.in_force,
            percent_in_force=c.percent_in_force,
            counts={state.value: n for state, n in c.counts.items()},
            items=[CompletenessItemResponse.from_item(i) for i in c.items],
        )


@router.get("/requirements", response_model=list[RequirementResponse])
async def list_requirements(_: CurrentUser, request: Request) -> list[RequirementResponse]:
    views = await request.app.state.list_pims_requirements.execute()
    return [RequirementResponse.from_view(v) for v in views]


@router.get("/completeness", response_model=CompletenessResponse)
async def completeness(_: CurrentUser, request: Request) -> CompletenessResponse:
    result = await request.app.state.get_pims_completeness.execute()
    return CompletenessResponse.from_domain(result)
