from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

DEFAULT_PASS_SCORE = 70
REVEAL_AFTER_ATTEMPTS = 3


class ExerciseKind(StrEnum):
    ORDERING = "ordering"
    MATCHING = "matching"
    SINGLE_CHOICE = "single_choice"
    QUIZ = "quiz"
    BRANCHING = "branching"
    SOA_FORM = "soa_form"
    DOCUMENT_FORM = "document_form"
    RISK_TABLE = "risk_table"
    TREATMENT_TABLE = "treatment_table"
    AUDIT_CHECKLIST = "audit_checklist"
    NONCONFORMITY_FORM = "nonconformity_form"
    COMPETENCE_MATRIX = "competence_matrix"


class EnrollmentStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ModuleStatus(StrEnum):
    LOCKED = "locked"
    AVAILABLE = "available"
    COMPLETED = "completed"


class RouteStatus(StrEnum):
    LOCKED = "locked"
    AVAILABLE = "available"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass(frozen=True)
class Route:
    code: str
    order: int
    title: str
    description: str
    hours: int
    prerequisite_code: str | None


@dataclass(frozen=True)
class ExerciseDef:
    """Ejercicio de un modulo. Si `generator` esta definido, `spec` se genera desde la BD."""

    kind: ExerciseKind
    spec: dict[str, Any] = field(default_factory=dict)
    generator: str | None = None
    params: dict[str, Any] = field(default_factory=dict)
    pass_score: int = DEFAULT_PASS_SCORE


@dataclass(frozen=True)
class Module:
    id: UUID
    route_code: str
    slug: str
    order: int
    title: str
    minutes: int
    mandatory: bool
    is_final: bool
    lesson_md: str
    exercise: ExerciseDef | None
    # Modulo previsto pero aun sin desarrollar: se lista, no es accesible ni obligatorio.
    planned: bool = False
    reference_title: str | None = None
    reference_md: str | None = None


@dataclass(frozen=True)
class Enrollment:
    user_id: UUID
    route_code: str
    status: EnrollmentStatus
    started_at: datetime
    completed_at: datetime | None = None


@dataclass(frozen=True)
class ModuleProgress:
    user_id: UUID
    module_id: UUID
    best_score: int
    completed: bool
    minutes_credited: int
    completed_at: datetime | None = None


@dataclass(frozen=True)
class ExerciseAttempt:
    id: UUID
    user_id: UUID
    module_id: UUID
    answer: dict[str, Any]
    score: int
    passed: bool
    created_at: datetime
