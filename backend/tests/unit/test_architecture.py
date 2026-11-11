"""AC-001-5: el dominio y la capa de aplicacion no dependen de frameworks de I/O."""

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src" / "unsa_audit"
FORBIDDEN = {"fastapi", "starlette", "sqlalchemy", "asyncpg", "subprocess", "alembic", "uvicorn"}


def _inner_layer_files() -> list[Path]:
    files: list[Path] = []
    for layer in ("domain", "application"):
        files += [p for p in SRC.rglob("*.py") if layer in p.relative_to(SRC).parts[:-1]]
    return files


def _imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            roots.add(node.module.split(".")[0])
    return roots


@pytest.mark.ac("AC-001-5")
def test_hay_capas_internas_que_verificar() -> None:
    assert _inner_layer_files(), "se esperaba al menos un archivo en domain/application"


@pytest.mark.ac("AC-001-5")
def test_domain_y_application_no_importan_frameworks() -> None:
    violations = {
        str(p.relative_to(SRC)): sorted(_imported_roots(p) & FORBIDDEN)
        for p in _inner_layer_files()
        if _imported_roots(p) & FORBIDDEN
    }
    assert not violations, f"imports prohibidos: {violations}"
