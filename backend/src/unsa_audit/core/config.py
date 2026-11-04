from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuracion de la aplicacion. Las variables obligatorias no tienen default."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str
    superadmin_email: str
    # Solo lo usa el seed para crear la cuenta superadmin (el registro publico la rechaza).
    superadmin_password: str | None = None
    jwt_secret: str = Field(min_length=16)
    jwt_expire_minutes: int = 120

    agy_command: str = "agy"
    agy_args: str = "--output-format json --mode plan --sandbox --effort low"
    agy_timeout_seconds: int = 120

    cors_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # pyright: ignore[reportCallIssue]
