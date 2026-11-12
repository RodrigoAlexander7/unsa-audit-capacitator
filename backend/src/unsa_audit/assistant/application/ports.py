"""Puertos de aplicacion del modulo assistant."""

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from unsa_audit.assistant.domain.entities import AssistantMessage, PromptContext


@dataclass(frozen=True)
class ModelAnswer:
    text: str
    duration_ms: int


class AssistantModelPort(Protocol):
    async def ask(self, prompt: str) -> ModelAnswer:
        """Lanza AssistantTimeout o AssistantUnavailable si el modelo falla."""
        ...


class StudentContextProvider(Protocol):
    async def build(self, module_id: UUID | None, route_path: str | None) -> PromptContext: ...


class AssistantHistoryRepository(Protocol):
    async def add(self, message: AssistantMessage) -> None: ...

    async def list_by_user(
        self, user_id: UUID, role: str, limit: int
    ) -> list[AssistantMessage]: ...

    async def clear_by_user(self, user_id: UUID, role: str) -> int: ...
