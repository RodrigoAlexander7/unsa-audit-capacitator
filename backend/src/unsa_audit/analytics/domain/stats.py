"""Estadisticas agregadas (sin datos personales) y reglas puras."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

MIN_ATTEMPTS_FOR_DIFFICULTY = 3
STALLED_DAYS = 7


def percent(part: int | float, total: int | float) -> int:
    return int((100 * part + total / 2) // total) if total else 0


@dataclass(frozen=True)
class RouteStats:
    code: str
    order: int
    title: str
    hours: int
    modules_total: int  # modulos publicados
    enrolled: int
    in_progress: int
    completed: int
    completion_rate: int  # % de matriculados que completaron
    avg_progress: int  # % medio de modulos publicados completados por matriculado
    avg_hours_credited: float
    attempts: int
    pass_rate: int  # % de intentos aprobados
    stalled: int  # en curso sin intentos en los ultimos STALLED_DAYS dias


@dataclass(frozen=True)
class ModuleStats:
    id: UUID
    route_code: str
    order: int
    title: str
    minutes: int
    is_final: bool
    attempts: int
    learners_attempted: int
    learners_completed: int
    avg_score: int | None
    pass_rate: int | None
    hardest: bool = False


@dataclass(frozen=True)
class GroupAverage:
    key: str
    label: str
    average: int  # % de aciertos acumulado
    samples: int  # evaluaciones consideradas


@dataclass(frozen=True)
class AssessmentProfileStats:
    profile: str
    finished: int
    avg_score: int
    pass_rate: int
    competencies: list[GroupAverage] = field(default_factory=list)
    requirements: list[GroupAverage] = field(default_factory=list)


@dataclass(frozen=True)
class ParticipantCounts:
    total: int
    new_last_7_days: int


@dataclass(frozen=True)
class AdvisorQuery:
    id: UUID
    asked_by: UUID | None
    question: str
    snapshot_hash: str
    status: str  # ok | error
    answer: str | None
    error: str | None
    duration_ms: int
    created_at: datetime


def hardest_modules(
    modules: list[ModuleStats], limit: int = 3, min_attempts: int = MIN_ATTEMPTS_FOR_DIFFICULTY
) -> set[UUID]:
    """Modulos con menor tasa de aprobacion (y menor puntaje) con intentos suficientes."""
    candidates = [m for m in modules if m.attempts >= min_attempts and m.pass_rate is not None]
    candidates.sort(key=lambda m: (m.pass_rate or 0, m.avg_score or 0, m.route_code, m.order))
    # Solo cuentan como "dificiles" los que no estan perfectos.
    return {m.id for m in candidates[:limit] if (m.pass_rate or 0) < 100}
