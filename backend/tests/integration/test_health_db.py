"""Requiere Postgres arriba (docker compose up -d db) y .env configurado."""

import httpx
import pytest

from unsa_audit.core.config import get_settings
from unsa_audit.main import create_app

pytestmark = pytest.mark.integration


@pytest.mark.ac("AC-001-1")
@pytest.mark.ac("AC-001-3")
async def test_health_con_postgres_real() -> None:
    app = create_app(get_settings())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "up"}
