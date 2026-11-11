import re
from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Role(StrEnum):
    LEARNER = "learner"
    SUPERADMIN = "superadmin"


@dataclass(frozen=True)
class User:
    id: UUID
    email: str
    full_name: str
    role: Role
    password_hash: str

    @property
    def is_superadmin(self) -> bool:
        return self.role is Role.SUPERADMIN


def normalize_email(raw: str) -> str:
    return raw.strip().lower()


def is_valid_email(email: str) -> bool:
    return bool(_EMAIL_RE.match(email)) and len(email) <= 254


def is_valid_password(password: str) -> bool:
    return MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH
