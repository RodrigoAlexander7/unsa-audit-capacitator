from uuid import UUID

from unsa_audit.identity.domain.user import User


class InMemoryUserRepository:
    def __init__(self) -> None:
        self.users: dict[UUID, User] = {}

    async def get_by_email(self, email: str) -> User | None:
        return next((u for u in self.users.values() if u.email == email), None)

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self.users.get(user_id)

    async def save(self, user: User) -> None:
        self.users[user.id] = user


class FakeHasher:
    """Hasher determinista y rapido solo para tests de casos de uso."""

    def hash(self, plain: str) -> str:
        return f"hashed::{plain}"

    def verify(self, plain: str, hashed: str) -> bool:
        return hashed == f"hashed::{plain}"
