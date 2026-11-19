"""Router HTTP para el modo administrador del asistente y borradores de reestructuracion."""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from unsa_audit.assistant.application.errors import (
    AssistantUnavailable,
    InvalidAssistantQuestion,
    InvalidProposalStatus,
    ProposalNotFound,
)
from unsa_audit.assistant.domain.admin_cohort import CurriculumProposal
from unsa_audit.assistant.domain.entities import MAX_ASSISTANT_QUESTION_CHARS
from unsa_audit.assistant.interface.router import (
    AssistantMessageResponse,
    ClearHistoryResponse,
)
from unsa_audit.identity.interface.dependencies import SuperAdmin

admin_router = APIRouter(prefix="/assistant/admin", tags=["assistant-admin"])


class CohortAliasItemResponse(BaseModel):
    alias: str
    full_name: str
    email: str
    stalled: bool
    overall_progress_pct: int


class CohortSummaryResponse(BaseModel):
    total_learners: int
    stalled_count: int
    aliases: list[CohortAliasItemResponse]


class AdminAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=MAX_ASSISTANT_QUESTION_CHARS)


class AdminAskResponse(BaseModel):
    message: AssistantMessageResponse
    aliases: list[CohortAliasItemResponse]


class GenerateProposalsRequest(BaseModel):
    focus: str | None = Field(default=None, max_length=400)
    route_code: str | None = Field(default=None, max_length=40)


class CurriculumProposalResponse(BaseModel):
    id: str
    title: str
    target_route_code: str | None
    target_module_slug: str | None
    change_type: str
    proposed_change: str
    rationale: str
    evidence_metrics: dict[str, Any]
    status: str
    review_note: str | None
    created_at: datetime
    reviewed_at: datetime | None

    @classmethod
    def from_domain(cls, p: CurriculumProposal) -> "CurriculumProposalResponse":
        return cls(
            id=str(p.id),
            title=p.title,
            target_route_code=p.target_route_code,
            target_module_slug=p.target_module_slug,
            change_type=p.change_type,
            proposed_change=p.proposed_change,
            rationale=p.rationale,
            evidence_metrics=p.evidence_metrics,
            status=p.status,
            review_note=p.review_note,
            created_at=p.created_at,
            reviewed_at=p.reviewed_at,
        )


class GenerateProposalsResponse(BaseModel):
    summary: str
    proposals: list[CurriculumProposalResponse]


class ReviewProposalRequest(BaseModel):
    status: str = Field(pattern="^(draft|accepted|discarded)$")
    review_note: str | None = Field(default=None, max_length=600)


def _alias_items(learners) -> list[CohortAliasItemResponse]:
    return [CohortAliasItemResponse(**lr.to_alias_info()) for lr in learners]


@admin_router.get("/cohort", response_model=CohortSummaryResponse)
async def cohort_summary(_: SuperAdmin, request: Request) -> CohortSummaryResponse:
    snapshot = await request.app.state.get_admin_cohort_summary.execute()
    aliases = _alias_items(snapshot.learners)
    return CohortSummaryResponse(
        total_learners=len(aliases),
        stalled_count=sum(1 for a in aliases if a.stalled),
        aliases=aliases,
    )


@admin_router.post("/ask", response_model=AdminAskResponse)
async def ask_admin(body: AdminAskRequest, admin: SuperAdmin, request: Request) -> AdminAskResponse:
    try:
        message, snapshot = await request.app.state.ask_admin_assistant.execute(
            admin.id, body.question
        )
    except InvalidAssistantQuestion as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
    except AssistantUnavailable as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            str(exc) or "El asistente administrador no está disponible en este momento.",
        ) from exc
    return AdminAskResponse(
        message=AssistantMessageResponse.from_domain(message),
        aliases=_alias_items(snapshot.learners),
    )


@admin_router.get("/history", response_model=list[AssistantMessageResponse])
async def admin_history(
    admin: SuperAdmin,
    request: Request,
    limit: int = Query(default=30, ge=1, le=50),
) -> list[AssistantMessageResponse]:
    items = await request.app.state.list_admin_history.execute(admin.id, limit=limit)
    return [AssistantMessageResponse.from_domain(item) for item in items]


@admin_router.delete("/history", response_model=ClearHistoryResponse)
async def clear_admin_history(admin: SuperAdmin, request: Request) -> ClearHistoryResponse:
    deleted = await request.app.state.clear_admin_history.execute(admin.id)
    return ClearHistoryResponse(deleted=deleted)


@admin_router.post(
    "/proposals/generate",
    response_model=GenerateProposalsResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_proposals(
    admin: SuperAdmin,
    request: Request,
    body: GenerateProposalsRequest | None = None,
) -> GenerateProposalsResponse:
    req = body or GenerateProposalsRequest()
    try:
        summary, proposals = await request.app.state.generate_restructuring_proposals.execute(
            admin.id, focus=req.focus, route_code=req.route_code
        )
    except AssistantUnavailable as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            str(exc) or "No se pudo generar una propuesta válida en este momento.",
        ) from exc
    return GenerateProposalsResponse(
        summary=summary,
        proposals=[CurriculumProposalResponse.from_domain(p) for p in proposals],
    )


@admin_router.get("/proposals", response_model=list[CurriculumProposalResponse])
async def list_proposals(
    _: SuperAdmin,
    request: Request,
    limit: int = Query(default=30, ge=1, le=50),
) -> list[CurriculumProposalResponse]:
    items = await request.app.state.list_curriculum_proposals.execute(limit=limit)
    return [CurriculumProposalResponse.from_domain(p) for p in items]


@admin_router.patch("/proposals/{proposal_id}", response_model=CurriculumProposalResponse)
async def review_proposal(
    proposal_id: UUID,
    body: ReviewProposalRequest,
    _: SuperAdmin,
    request: Request,
) -> CurriculumProposalResponse:
    try:
        updated = await request.app.state.review_curriculum_proposal.execute(
            proposal_id, body.status, review_note=body.review_note
        )
    except ProposalNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidProposalStatus as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
    return CurriculumProposalResponse.from_domain(updated)
