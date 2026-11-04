"""Requisitos documentales del PIMS y su estado de cumplimiento (puro)."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from uuid import UUID

from unsa_audit.documents.domain.documents import DocumentKind, DocumentLifecycle


class RequirementState(StrEnum):
    IN_FORCE = "in_force"
    DRAFT = "draft"
    EXPIRED = "expired"
    UNOWNED = "unowned"
    MISSING = "missing"


# Precedencia: el primer problema de la lista define el estado.
_PRECEDENCE = (
    RequirementState.MISSING,
    RequirementState.DRAFT,
    RequirementState.EXPIRED,
    RequirementState.UNOWNED,
)


@dataclass(frozen=True)
class PimsRequirement:
    id: UUID
    code: str
    clause_ref: str  # dato: la numeracion depende de la edicion de la norma
    title: str
    document_kind: DocumentKind
    summary: str
    expected_evidence: str
    responsible_unit_code: str | None
    sort_order: int


@dataclass(frozen=True)
class StateEvaluation:
    state: RequirementState
    issues: tuple[RequirementState, ...]


def evaluate_state(
    *,
    exists: bool,
    lifecycle: DocumentLifecycle | None,
    review_date: date | None,
    owner_unit_code: str | None,
    today: date,
) -> StateEvaluation:
    """Estado de un requisito segun el documento que lo cubre (o su ausencia)."""
    if not exists:
        return StateEvaluation(RequirementState.MISSING, (RequirementState.MISSING,))

    issues: list[RequirementState] = []
    if lifecycle is DocumentLifecycle.DRAFT:
        issues.append(RequirementState.DRAFT)
    # `expired` solo aplica a documentos vigentes (un borrador no "vence").
    if lifecycle is DocumentLifecycle.IN_FORCE and review_date is not None and review_date < today:
        issues.append(RequirementState.EXPIRED)
    if not owner_unit_code:
        issues.append(RequirementState.UNOWNED)

    if issues:
        state = next(s for s in _PRECEDENCE if s in issues)
        return StateEvaluation(state, tuple(issues))
    return StateEvaluation(RequirementState.IN_FORCE, ())


def percent(part: int, total: int) -> int:
    return (100 * part + total // 2) // total if total else 0
