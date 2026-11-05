"""Entidades puras del asistente del estudiante."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID

MAX_ASSISTANT_QUESTION_CHARS = 800
MAX_ROUTE_PATH_CHARS = 200
MAX_LESSON_EXCERPT_CHARS = 1800
MAX_REFERENCE_EXCERPT_CHARS = 1200


class AssistantRole(StrEnum):
    STUDENT = "student"
    ADMIN = "admin"


class AssistantStatus(StrEnum):
    OK = "ok"
    REFUSED = "refused"
    ERROR = "error"


@dataclass(frozen=True)
class PromptContext:
    """Contexto acotado y seguro para el asistente (sin PII estudiantil ni soluciones)."""

    route_path: str | None = None
    route_title: str | None = None
    module_id: UUID | None = None
    module_title: str | None = None
    has_exercise: bool = False
    lesson_excerpt: str | None = None
    reference_excerpt: str | None = None
    unsa_units: tuple[dict[str, str], ...] = ()
    unsa_positions: tuple[dict[str, str], ...] = ()
    unsa_systems: tuple[dict[str, object], ...] = ()
    unsa_activities: tuple[dict[str, str], ...] = ()
    pims_docs: tuple[dict[str, str | None], ...] = ()
    extra: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class AssistantMessage:
    id: UUID
    user_id: UUID
    role: str
    module_id: UUID | None
    route_path: str | None
    question: str
    status: str
    answer: str | None
    error: str | None
    context_hash: str
    duration_ms: int
    created_at: datetime
