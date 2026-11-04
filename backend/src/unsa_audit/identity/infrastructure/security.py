from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from argon2 import PasswordHasher as _Argon2
from argon2.exceptions import InvalidHashError, VerificationError

from unsa_audit.identity.application.ports import TokenClaims
from unsa_audit.identity.domain.errors import InvalidToken
from unsa_audit.identity.domain.user import Role


class Argon2PasswordHasher:
    def __init__(self) -> None:
        self._hasher = _Argon2()

    def hash(self, plain: str) -> str:
        return self._hasher.hash(plain)

    def verify(self, plain: str, hashed: str) -> bool:
        try:
            return self._hasher.verify(hashed, plain)
        except (VerificationError, InvalidHashError):
            return False


class JwtTokenService:
    _ALGORITHM = "HS256"

    def __init__(self, secret: str, expire_minutes: int) -> None:
        self._secret = secret
        self._expire = timedelta(minutes=expire_minutes)

    def issue(self, user_id: UUID, role: Role) -> str:
        now = datetime.now(UTC)
        payload = {"sub": str(user_id), "role": role.value, "iat": now, "exp": now + self._expire}
        return jwt.encode(payload, self._secret, algorithm=self._ALGORITHM)

    def decode(self, token: str) -> TokenClaims:
        try:
            payload = jwt.decode(
                token,
                self._secret,
                algorithms=[self._ALGORITHM],
                options={"require": ["exp", "sub"]},
            )
            return TokenClaims(user_id=UUID(payload["sub"]), role=Role(payload["role"]))
        except (jwt.PyJWTError, ValueError, KeyError) as exc:
            raise InvalidToken from exc
