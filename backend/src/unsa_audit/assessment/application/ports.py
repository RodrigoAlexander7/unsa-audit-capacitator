from typing import Protocol
from uuid import UUID

from unsa_audit.assessment.domain.assessment import AssessmentDefinition, Attempt, Profile


class QuestionBank(Protocol):
    def get(self, profile: Profile) -> AssessmentDefinition | None: ...


class AssessmentRepository(Protocol):
    async def add(self, attempt: Attempt) -> None: ...

    async def get(self, attempt_id: UUID) -> Attempt | None: ...

    async def save(self, attempt: Attempt) -> bool:
        """Guarda la correccion solo si el intento seguia en curso. False si ya estaba enviado."""
        ...

    async def list_for_user(self, user_id: UUID) -> list[Attempt]:
        """Mas recientes primero."""
        ...


class RequirementCatalog(Protocol):
    async def labels(self) -> dict[str, str]:
        """codigo de requisito PIMS -> '<clausula> <titulo>'."""
        ...
