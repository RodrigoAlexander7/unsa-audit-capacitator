"""Router FastAPI del asistente del estudiante."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from unsa_audit.assistant.application.errors import (
    AssistantUnavailable,
    InvalidAssistantQuestion,
)
from unsa_audit.assistant.domain.entities import (
    MAX_ASSISTANT_QUESTION_CHARS,
    MAX_ROUTE_PATH_CHARS,
    AssistantMessage,
)
from unsa_audit.identity.interface.dependencies import CurrentUser

router = APIRouter(prefix="/assistant", tags=["assistant"])


class AssistantAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=MAX_ASSISTANT_QUESTION_CHARS)
    module_id: UUID | None = None
    route_path: str | None = Field(default=None, max_length=MAX_ROUTE_PATH_CHARS)


class AssistantMessageResponse(BaseModel):
    id: str
    question: str
    status: str
    answer: str | None
    error: str | None
    module_id: str | None
    route_path: str | None
    context_hash: str
    duration_ms: int
    created_at: datetime

    @classmethod
    def from_domain(cls, m: AssistantMessage) -> "AssistantMessageResponse":
        return cls(
            id=str(m.id),
            question=m.question,
            status=m.status,
            answer=m.answer,
            error=m.error,
            module_id=str(m.module_id) if m.module_id else None,
            route_path=m.route_path,
            context_hash=m.context_hash,
            duration_ms=m.duration_ms,
            created_at=m.created_at,
        )


class ClearHistoryResponse(BaseModel):
    deleted: int


@router.post("/ask", response_model=AssistantMessageResponse)
async def ask(
    body: AssistantAskRequest, user: CurrentUser, request: Request
) -> AssistantMessageResponse:
    try:
        message = await request.app.state.ask_student_assistant.execute(
            user.id,
            body.question,
            module_id=body.module_id,
            raw_route_path=body.route_path,
        )
    except InvalidAssistantQuestion as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
    except AssistantUnavailable as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            str(exc) or "El asistente no está disponible en este momento.",
        ) from exc
    return AssistantMessageResponse.from_domain(message)


@router.get("/history", response_model=list[AssistantMessageResponse])
async def history(
    user: CurrentUser,
    request: Request,
    limit: int = Query(default=30, ge=1, le=50),
) -> list[AssistantMessageResponse]:
    items = await request.app.state.list_student_history.execute(user.id, limit=limit)
    return [AssistantMessageResponse.from_domain(item) for item in items]


@router.delete("/history", response_model=ClearHistoryResponse)
async def clear_history(user: CurrentUser, request: Request) -> ClearHistoryResponse:
    deleted = await request.app.state.clear_student_history.execute(user.id)
    return ClearHistoryResponse(deleted=deleted)
