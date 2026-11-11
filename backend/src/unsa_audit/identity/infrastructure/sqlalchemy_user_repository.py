from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from unsa_audit.identity.domain.user import Role, User
from unsa_audit.identity.infrastructure.models import UserModel


def _to_domain(model: UserModel) -> User:
    return User(
        id=model.id,
        email=model.email,
        full_name=model.full_name,
        role=Role(model.role),
        password_hash=model.password_hash,
    )


class SqlAlchemyUserRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_email(self, email: str) -> User | None:
        async with self._session_factory() as session:
            result = await session.execute(select(UserModel).where(UserModel.email == email))
            model = result.scalar_one_or_none()
            return _to_domain(model) if model else None

    async def get_by_id(self, user_id: UUID) -> User | None:
        async with self._session_factory() as session:
            model = await session.get(UserModel, user_id)
            return _to_domain(model) if model else None

    async def save(self, user: User) -> None:
        async with self._session_factory() as session, session.begin():
            model = await session.get(UserModel, user.id)
            if model is None:
                session.add(
                    UserModel(
                        id=user.id,
                        email=user.email,
                        full_name=user.full_name,
                        role=user.role.value,
                        password_hash=user.password_hash,
                    )
                )
            else:
                model.email = user.email
                model.full_name = user.full_name
                model.role = user.role.value
                model.password_hash = user.password_hash
