"""AC-003-15: el contenido de `content/routes` es valido y coherente."""

import json
from pathlib import Path

import pytest

from tests.solutions import solve
from tests.unit.fakes_learning import snapshot_from_dataset
from unsa_audit.learning.application.generators import generate_spec
from unsa_audit.learning.domain.exercises import grade, to_public, validate_spec
from unsa_audit.learning.infrastructure.content_loader import ContentError, FileContentSource

CONTENT = Path(__file__).resolve().parents[3] / "content"


@pytest.fixture(scope="module")
def loaded():
    return FileContentSource(CONTENT).load()


@pytest.mark.ac("AC-003-15")
def test_catalogo_con_cuatro_rutas_y_prerrequisitos_encadenados(loaded) -> None:
    routes, _ = loaded
    by_order = sorted(routes, key=lambda r: r.order)
    assert [(r.code, r.hours) for r in by_order] == [
        ("sensibilizacion", 12), ("interpretacion", 16), ("implementacion", 24), ("auditor", 32),
    ]  # fmt: skip
    assert [r.prerequisite_code for r in by_order] == [
        None, "sensibilizacion", "interpretacion", "implementacion",
    ]  # fmt: skip


@pytest.mark.ac("AC-003-15")
def test_ruta_1_suma_720_minutos_y_tiene_una_evaluacion_final(loaded) -> None:
    routes, modules = loaded
    r1 = [m for m in modules if m.route_code == "sensibilizacion"]
    assert len(r1) == 7
    assert (
        sum(m.minutes for m in r1)
        == next(r.hours for r in routes if r.code == "sensibilizacion") * 60
    )
    assert [m.order for m in r1] == list(range(1, 8))
    finals = [m for m in r1 if m.is_final]
    assert len(finals) == 1 and finals[0].order == 7
    assert all(m.exercise is not None for m in r1), "cada modulo de R1 lleva su ejercicio"
    assert all(m.lesson_md.startswith("#") for m in r1)


@pytest.mark.ac("AC-003-15")
def test_ids_de_modulo_unicos_y_estables(loaded) -> None:
    _, modules = loaded
    assert len({m.id for m in modules}) == len(modules)
    again = FileContentSource(CONTENT).load()[1]
    assert [m.id for m in modules] == [m.id for m in again]


@pytest.mark.ac("AC-003-15")
def test_todos_los_ejercicios_son_validos_y_resolubles_con_la_bd_del_seed(loaded) -> None:
    _, modules = loaded
    facts = snapshot_from_dataset()
    for module in modules:
        ex = module.exercise
        if ex is None:
            continue
        spec = generate_spec(ex.generator, ex.params, facts) if ex.generator else ex.spec
        validate_spec(ex.kind, spec)
        assert grade(ex.kind, spec, solve(ex.kind, spec)).score == 100, module.slug
        assert ex.pass_score <= 100
        public = to_public(ex.kind, spec, str(module.id))
        assert public["prompt"], module.slug


@pytest.mark.ac("AC-003-15")
def test_contenido_roto_se_rechaza(tmp_path: Path) -> None:
    route = tmp_path / "routes" / "1-x"
    route.mkdir(parents=True)
    (route / "route.yaml").write_text(
        "code: x\norder: 1\ntitle: X\nhours: 1\nprerequisite: null\n", encoding="utf-8"
    )
    (route / "01-a.md").write_text("---\ntitle: A\nminutes: 60\n---\n# A\n", encoding="utf-8")
    (route / "01-a.exercise.json").write_text(
        json.dumps({"kind": "single_choice",
                    "spec": {"prompt": "p", "options": [{"id": "a", "label": "A"},
                                                         {"id": "b", "label": "B"}],
                             "correct": "z"}}),
        encoding="utf-8",
    )  # fmt: skip
    with pytest.raises(ContentError, match="correct"):
        FileContentSource(tmp_path).load()

    (route / "01-a.exercise.json").write_text(
        json.dumps({"kind": "quiz", "generator": "inventado"}), encoding="utf-8"
    )
    with pytest.raises(ContentError, match="generador desconocido"):
        FileContentSource(tmp_path).load()

    (route / "01-a.exercise.json").unlink()
    (route / "01-a.md").write_text("sin frontmatter", encoding="utf-8")
    with pytest.raises(ContentError, match="frontmatter"):
        FileContentSource(tmp_path).load()
