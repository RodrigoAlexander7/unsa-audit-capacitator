import httpx
import pytest

from unsa_audit.core.config import Settings
from unsa_audit.health.application.check_health import CheckHealth
from unsa_audit.main import create_app


class FakeProbe:
    def __init__(self, up: bool) -> None:
        self._up = up

    async def is_up(self) -> bool:
        return self._up


def _settings() -> Settings:
    return Settings(  # pyright: ignore[reportCallIssue]
        _env_file=None,  # pyright: ignore[reportCallIssue]
        database_url="postgresql+asyncpg://u:p@localhost/db",
        superadmin_email="admin@example.test",
        jwt_secret="x" * 32,
    )


@pytest.mark.ac("AC-001-3")
async def test_caso_de_uso_reporta_ok_si_bd_responde() -> None:
    report = await CheckHealth(FakeProbe(True)).execute()
    assert report.status == "ok" and report.database_up


@pytest.mark.ac("AC-001-3")
async def test_endpoint_200_con_bd_arriba() -> None:
    app = create_app(_settings(), probe=FakeProbe(True))
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "up"}


@pytest.mark.ac("AC-001-3")
async def test_endpoint_503_con_bd_caida() -> None:
    app = create_app(_settings(), probe=FakeProbe(False))
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "down"}
