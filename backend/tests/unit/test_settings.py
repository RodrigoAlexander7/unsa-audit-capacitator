import pytest
from pydantic import ValidationError

from unsa_audit.core.config import Settings


@pytest.mark.ac("AC-001-4")
def test_falla_si_falta_superadmin_email(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SUPERADMIN_EMAIL", raising=False)
    with pytest.raises(ValidationError) as exc:
        Settings(  # pyright: ignore[reportCallIssue]
            _env_file=None,  # pyright: ignore[reportCallIssue]
            database_url="postgresql+asyncpg://u:p@localhost/db",
            jwt_secret="x" * 32,
        )
    assert "superadmin_email" in str(exc.value)


@pytest.mark.ac("AC-001-4")
def test_carga_con_config_completa() -> None:
    settings = Settings(  # pyright: ignore[reportCallIssue]
        _env_file=None,  # pyright: ignore[reportCallIssue]
        database_url="postgresql+asyncpg://u:p@localhost/db",
        superadmin_email="admin@example.test",
        jwt_secret="x" * 32,
    )
    assert settings.superadmin_email == "admin@example.test"
