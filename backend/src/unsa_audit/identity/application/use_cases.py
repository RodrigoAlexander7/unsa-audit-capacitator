from dataclasses import dataclass
from uuid import UUID, uuid4

from unsa_audit.identity.application.ports import PasswordHasher, TokenService, UserRepository
from unsa_audit.identity.domain.errors import (
    EmailNotAvailable,
    InvalidCredentials,
    InvalidRegistration,
    InvalidToken,
)
from unsa_audit.identity.domain.user import (
    Role,
    User,
    is_valid_email,
    is_valid_password,
    normalize_email,
)


class RegisterUser:
    """Registro publico: siempre crea un `learner`. El email superadmin esta reservado."""

    def __init__(
        self, users: UserRepository, hasher: PasswordHasher, superadmin_email: str
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._superadmin_email = normalize_email(superadmin_email)

    async def execute(self, email: str, password: str, full_name: str) -> User:
        email = normalize_email(email)
        full_name = full_name.strip()
        if not is_valid_email(email) or not is_valid_password(password) or not full_name:
            raise InvalidRegistration
        if email == self._superadmin_email:
            raise EmailNotAvailable
        if await self._users.get_by_email(email) is not None:
            raise EmailNotAvailable
        user = User(
            id=uuid4(),
            email=email,
            full_name=full_name,
            role=Role.LEARNER,
            password_hash=self._hasher.hash(password),
        )
        await self._users.save(user)
        return user


@dataclass(frozen=True)
class AuthResult:
    access_token: str
    user: User


class Login:
    def __init__(self, users: UserRepository, hasher: PasswordHasher, tokens: TokenService) -> None:
        self._users = users
        self._hasher = hasher
        self._tokens = tokens
        # Hash de relleno para igualar el tiempo de respuesta cuando el email no existe.
        self._dummy_hash = hasher.hash("dummy-password-for-timing")

    async def execute(self, email: str, password: str) -> AuthResult:
        user = await self._users.get_by_email(normalize_email(email))
        if user is None:
            self._hasher.verify(password, self._dummy_hash)
            raise InvalidCredentials
        if not self._hasher.verify(password, user.password_hash):
            raise InvalidCredentials
        return AuthResult(self._tokens.issue(user.id, user.role), user)


class GetCurrentUser:
    def __init__(self, users: UserRepository, tokens: TokenService) -> None:
        self._users = users
        self._tokens = tokens

    async def execute(self, token: str) -> User:
        claims = self._tokens.decode(token)
        user = await self._users.get_by_id(claims.user_id)
        if user is None:
            raise InvalidToken
        return user


class EnsureSuperadmin:
    """Crea (o repara) la cuenta superadmin a partir de la configuracion. Idempotente."""

    def __init__(
        self, users: UserRepository, hasher: PasswordHasher, email: str, password: str
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._email = normalize_email(email)
        self._password = password

    async def execute(self) -> User:
        existing = await self._users.get_by_email(self._email)
        user_id: UUID = existing.id if existing else uuid4()
        user = User(
            id=user_id,
            email=self._email,
            full_name=existing.full_name if existing else "Superadministrador",
            role=Role.SUPERADMIN,
            password_hash=self._hasher.hash(self._password),
        )
        await self._users.save(user)
        return user
