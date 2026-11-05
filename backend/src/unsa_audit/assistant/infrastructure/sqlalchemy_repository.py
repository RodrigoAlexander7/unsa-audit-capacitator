"""Repositorio SQLAlchemy aislado por usuario para el historial del asistente."""

from uuid import UUID

from sqlalchemy import CursorResult, delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from unsa_audit.assistant.domain.entities import AssistantMessage
from unsa_audit.assistant.infrastructure.models import AssistantMessageModel


class SqlAlchemyAssistantHistoryRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    async def add(self, message: AssistantMessage) -> None:
        async with self._sf() as session, session.begin():
            session.add(
                AssistantMessageModel(
                    id=message.id,
                    user_id=message.user_id,
                    role=message.role,
                    module_id=message.module_id,
                    route_path=message.route_path,
                    question=message.question,
                    status=message.status,
                    answer=message.answer,
                    error=message.error,
                    context_hash=message.context_hash,
                    duration_ms=message.duration_ms,
                    created_at=message.created_at,
                )
            )

    async def list_by_user(self, user_id: UUID, role: str, limit: int) -> list[AssistantMessage]:
        async with self._sf() as session:
            rows = await session.scalars(
                select(AssistantMessageModel)
                .where(
                    AssistantMessageModel.user_id == user_id,
                    AssistantMessageModel.role == role,
                )
                .order_by(AssistantMessageModel.created_at.desc())
                .limit(limit)
            )
            return [
                AssistantMessage(
                    id=r.id,
                    user_id=r.user_id,
                    role=r.role,
                    module_id=r.module_id,
                    route_path=r.route_path,
                    question=r.question,
                    status=r.status,
                    answer=r.answer,
                    error=r.error,
                    context_hash=r.context_hash,
                    duration_ms=r.duration_ms,
                    created_at=r.created_at,
                )
                for r in rows
            ]

    async def clear_by_user(self, user_id: UUID, role: str) -> int:
        async with self._sf() as session, session.begin():
            result = await session.execute(
                delete(AssistantMessageModel).where(
                    AssistantMessageModel.user_id == user_id,
                    AssistantMessageModel.role == role,
                )
            )
            cursor: CursorResult[tuple[()]] = result  # type: ignore[assignment]
            return int(cursor.rowcount or 0)
