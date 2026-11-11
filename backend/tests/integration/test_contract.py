"""AC-002-14 / AC-003-17: la API expone todo lo que declaran los contratos de las specs."""

from pathlib import Path

import pytest
import yaml

from unsa_audit.core.config import Settings
from unsa_audit.main import create_app

SPECS = Path(__file__).resolve().parents[3] / "specs"
CONTRACTS = sorted(SPECS.glob("*/contracts/openapi.yaml"))


def _settings() -> Settings:
    return Settings(  # pyright: ignore[reportCallIssue]
        _env_file=None,  # pyright: ignore[reportCallIssue]
        database_url="postgresql+asyncpg://u:p@localhost/db",
        superadmin_email="admin@example.test",
        jwt_secret="x" * 32,
    )


def test_hay_contratos_que_verificar() -> None:
    assert len(CONTRACTS) >= 2


@pytest.mark.ac("AC-002-14")
@pytest.mark.ac("AC-003-17")
@pytest.mark.parametrize("contract_path", CONTRACTS, ids=lambda p: p.parents[1].name)
def test_la_api_expone_paths_y_metodos_del_contrato(contract_path: Path) -> None:
    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    actual = create_app(_settings()).openapi()["paths"]
    problems: list[str] = []
    for path, methods in contract["paths"].items():
        for method, spec in methods.items():
            if method not in actual.get(path, {}):
                problems.append(f"falta {method.upper()} {path}")
                continue
            declared_ok = {c for c in spec["responses"] if c.startswith("2")}
            exposed = set(actual[path][method]["responses"])
            if not declared_ok & exposed:
                problems.append(f"{method.upper()} {path}: ninguna respuesta 2xx coincide")
    assert not problems, problems
