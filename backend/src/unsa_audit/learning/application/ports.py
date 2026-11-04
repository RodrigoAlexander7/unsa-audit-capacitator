from dataclasses import dataclass, field
from typing import Protocol
from uuid import UUID

from unsa_audit.learning.domain.route import (
    Enrollment,
    ExerciseAttempt,
    Module,
    ModuleProgress,
    Route,
)


@dataclass(frozen=True)
class UnitFact:
    code: str
    name: str
    kind: str


@dataclass(frozen=True)
class PositionFact:
    title: str
    unit_kind: str


@dataclass(frozen=True)
class SystemFact:
    name: str
    owner_unit_name: str


@dataclass(frozen=True)
class UniversitySnapshot:
    """Hechos de la UNSA ficticia que alimentan los ejercicios generados."""

    units: list[UnitFact] = field(default_factory=list)
    positions: list[PositionFact] = field(default_factory=list)
    systems: list[SystemFact] = field(default_factory=list)


class UniversityFacts(Protocol):
    async def snapshot(self) -> UniversitySnapshot: ...


class ContentSource(Protocol):
    def load(self) -> tuple[list[Route], list[Module]]: ...


class LearningRepository(Protocol):
    async def replace_content(self, routes: list[Route], modules: list[Module]) -> None:
        """Upsert de rutas y modulos; elimina los modulos que ya no estan en el contenido."""
        ...

    async def list_routes(self) -> list[Route]: ...

    async def get_route(self, code: str) -> Route | None: ...

    async def list_modules(self, route_code: str | None = None) -> list[Module]:
        """Modulos ordenados por (ruta, orden). Sin argumento, todos."""
        ...

    async def get_module(self, module_id: UUID) -> Module | None: ...

    async def get_enrollment(self, user_id: UUID, route_code: str) -> Enrollment | None: ...

    async def list_enrollments(self, user_id: UUID) -> list[Enrollment]: ...

    async def save_enrollment(self, enrollment: Enrollment) -> None: ...

    async def list_progress(self, user_id: UUID) -> dict[UUID, ModuleProgress]:
        """Progreso del usuario indexado por module_id (todas las rutas)."""
        ...

    async def save_progress(self, progress: ModuleProgress) -> None: ...

    async def add_attempt(self, attempt: ExerciseAttempt) -> None: ...
