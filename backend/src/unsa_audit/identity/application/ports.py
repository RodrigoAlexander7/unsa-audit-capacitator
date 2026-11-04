from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from unsa_audit.identity.domain.user import Role, User


class UserRepository(Protocol):
    async def get_by_email(self, email: str) -> User | None: ...

    async def get_by_id(self, user_id: UUID) -> User | None: ...

    async def save(self, user: User) -> None:
        """Inserta o actualiza (upsert por id)."""
        ...


class PasswordHasher(Protocol):
    def hash(self, plain: str) -> str: ...

    def verify(self, plain: str, hashed: str) -> bool: ...


@dataclass(frozen=True)
class TokenClaims:
    user_id: UUID
    role: Role


class TokenService(Protocol):
    def issue(self, user_id: UUID, role: Role) -> str: ...

    def decode(self, token: str) -> TokenClaims:
        """Lanza InvalidToken si el token no es valido o expiro."""
        ...
