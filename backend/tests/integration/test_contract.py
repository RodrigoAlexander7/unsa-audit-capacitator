"""AC-002-14: la API expone todo lo que declara el contrato de la spec."""

from pathlib import Path

import pytest
import yaml

from unsa_audit.core.config import Settings
from unsa_audit.main import create_app

pytestmark = pytest.mark.ac("AC-002-14")

CONTRACT = (
    Path(__file__).resolve().parents[3] / "specs" / "002-identity-university" / "contracts"
    / "openapi.yaml"
)  # fmt: skip


def _settings() -> Settings:
    return Settings(  # pyright: ignore[reportCallIssue]
        _env_file=None,  # pyright: ignore[reportCallIssue]
        database_url="postgresql+asyncpg://u:p@localhost/db",
        superadmin_email="admin@example.test",
        jwt_secret="x" * 32,
    )


def test_la_api_expone_paths_y_metodos_del_contrato() -> None:
    contract = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    actual = create_app(_settings()).openapi()["paths"]
    missing = []
    for path, methods in contract["paths"].items():
        for method, spec in methods.items():
            if method not in actual.get(path, {}):
                missing.append(f"{method.upper()} {path}")
                continue
            declared = set(spec["responses"])
            exposed = set(actual[path][method]["responses"])
            assert "200" in exposed or "201" in exposed
            # las respuestas de exito del contrato deben existir en la API
            assert {c for c in declared if c.startswith("2")} <= exposed, f"{method} {path}"
    assert not missing, f"faltan en la API: {missing}"
