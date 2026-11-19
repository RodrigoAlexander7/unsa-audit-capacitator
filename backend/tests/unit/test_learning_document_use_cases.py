"""Tests unitarios de aplicacion e infraestructura para practica documental (Spec 009)."""

from datetime import UTC, date, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from tests.solutions import solve, wrong
from tests.unit.fakes_learning import FakeFacts, InMemoryLearningRepository, pims_facts
from unsa_audit.learning.application.generators import generate_spec
from unsa_audit.learning.application.ports import UniversitySnapshot
from unsa_audit.learning.application.use_cases import EnrollInRoute, SubmitAttempt
from unsa_audit.learning.domain.exercises import InvalidExerciseSpec, grade, validate_spec
from unsa_audit.learning.domain.route import ExerciseDef, ExerciseKind, Module, Route
from unsa_audit.learning.infrastructure.content_loader import ContentError, FileContentSource

NOW = datetime(2026, 6, 1, tzinfo=UTC)
CONTENT = Path(__file__).resolve().parents[3] / "content"


@pytest.mark.ac("AC-009-6")
def test_audit_checklist_from_pims_genera_desde_estado_real() -> None:
    facts = UniversitySnapshot(pims=pims_facts())
    spec = generate_spec("audit_checklist_from_pims", {}, facts)
    validate_spec(ExerciseKind.AUDIT_CHECKLIST, spec)
    assert len(spec["items"]) == 11

    by_id = {it["id"]: it for it in spec["items"]}
    assert by_id["pims-alcance"]["expected_verdict"] == "conforme"
    assert by_id["pims-plan-tratamiento"]["expected_verdict"] == "observacion"
    assert by_id["pims-soa"]["expected_verdict"] == "no_conformidad"
    assert by_id["pims-monitoreo"]["expected_verdict"] == "no_conformidad"
    assert (
        grade(ExerciseKind.AUDIT_CHECKLIST, spec, solve(ExerciseKind.AUDIT_CHECKLIST, spec)).score
        == 100
    )

    # Cambia al avanzar el reloj -> todos los vigentes vencen
    later = UniversitySnapshot(pims=pims_facts(today=date(2031, 1, 1)))
    spec_later = generate_spec("audit_checklist_from_pims", {}, later)
    assert all(it["expected_verdict"] != "conforme" for it in spec_later["items"])

    with pytest.raises(InvalidExerciseSpec):
        generate_spec("audit_checklist_from_pims", {}, UniversitySnapshot())


@pytest.mark.ac("AC-009-9")
async def test_politica_de_revelacion_tras_3_intentos_fallidos() -> None:
    from tests.unit.test_document_exercises import COMPETENCE_SPEC

    route = Route("r3", 3, "Implementación", "", 24, None)
    mod = Module(
        id=uuid4(),
        route_code="r3",
        slug="competencia",
        order=1,
        title="Matriz de competencia",
        minutes=120,
        mandatory=True,
        is_final=False,
        lesson_md="# Lección",
        exercise=ExerciseDef(ExerciseKind.COMPETENCE_MATRIX, COMPETENCE_SPEC, pass_score=70),
    )
    repo = InMemoryLearningRepository([route], [mod])
    user = uuid4()
    await EnrollInRoute(repo, clock=lambda: NOW).execute(user, "r3")
    submit = SubmitAttempt(repo, FakeFacts(), clock=lambda: NOW)

    bad = wrong(ExerciseKind.COMPETENCE_MATRIX)
    r1 = await submit.execute(user, mod.id, bad)
    assert (r1.attempt_number, r1.passed, r1.solution_revealed, r1.solution_guide) == (
        1,
        False,
        False,
        (),
    )

    r2 = await submit.execute(user, mod.id, bad)
    assert (r2.attempt_number, r2.passed, r2.solution_revealed, r2.solution_guide) == (
        2,
        False,
        False,
        (),
    )

    r3 = await submit.execute(user, mod.id, bad)
    assert (r3.attempt_number, r3.passed, r3.module_completed, r3.solution_revealed) == (
        3,
        False,
        False,
        True,
    )
    assert len(r3.solution_guide) == 1
    assert r3.solution_guide[0].id == "row-aud"

    # Debe seguir enviando una respuesta valida para aprobar
    r4 = await submit.execute(user, mod.id, solve(ExerciseKind.COMPETENCE_MATRIX, COMPETENCE_SPEC))
    assert (r4.attempt_number, r4.passed, r4.module_completed, r4.solution_revealed) == (
        4,
        True,
        True,
        False,
    )


@pytest.mark.ac("AC-009-10")
def test_content_loader_carga_reference_doc_y_sidecar(tmp_path: Path) -> None:
    inst = tmp_path / "institutional" / "pims-alcance"
    inst.mkdir(parents=True)
    (inst / "document.yaml").write_text(
        "code: pims-alcance\nkind: PIMS_SCOPE\ntitle: Alcance UNSA\n", encoding="utf-8"
    )
    (inst / "v1.md").write_text(
        "---\nmessage: v1\nauthor: OTI\ndate: 2026-01-01\n---\n# Alcance oficial\nContenido.",
        encoding="utf-8",
    )

    route_dir = tmp_path / "routes" / "2-interpretacion"
    route_dir.mkdir(parents=True)
    (route_dir / "route.yaml").write_text(
        "code: interpretacion\norder: 2\ntitle: R2\nhours: 16\n", encoding="utf-8"
    )
    (route_dir / "01-alcance.md").write_text(
        "---\ntitle: Alcance\nminutes: 60\nreference_doc: pims-alcance\n---\n# Alcance\n",
        encoding="utf-8",
    )
    (route_dir / "02-politica.md").write_text(
        "---\ntitle: Política\nminutes: 60\n---\n# Política\n", encoding="utf-8"
    )
    (route_dir / "02-politica.reference.md").write_text(
        "---\ntitle: Ejemplo Política UNSA\n---\n# Política resuelta\nTexto ejemplo.",
        encoding="utf-8",
    )

    _, modules = FileContentSource(tmp_path).load()
    assert len(modules) == 2  # no carga .reference.md como modulo
    assert modules[0].reference_title == "Alcance UNSA"
    assert modules[0].reference_md is not None and "# Alcance oficial" in modules[0].reference_md
    assert modules[1].reference_title == "Ejemplo Política UNSA"
    assert modules[1].reference_md is not None and "Texto ejemplo." in modules[1].reference_md

    # Error si reference_doc no existe
    (route_dir / "01-alcance.md").write_text(
        "---\ntitle: Alcance\nminutes: 60\nreference_doc: inexistente\n---\n# Alcance\n",
        encoding="utf-8",
    )
    with pytest.raises(ContentError, match="reference_doc"):
        FileContentSource(tmp_path).load()


@pytest.mark.ac("AC-009-10")
def test_contenido_real_carga_referencia_en_demo_r3() -> None:
    _, modules = FileContentSource(CONTENT).load()
    soa_mod = next(m for m in modules if m.slug == "declaracion-de-aplicabilidad")
    assert soa_mod.reference_title and "Biblioteca Central" in soa_mod.reference_title
    assert soa_mod.reference_md and "Biblioteca Digital" in soa_mod.reference_md
