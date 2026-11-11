from datetime import date
from pathlib import Path

import pytest

from tests.unit.fakes_documents import InMemoryDocumentRepository
from unsa_audit.documents.application.pims_use_cases import (
    GetPimsCompleteness,
    ListPimsRequirements,
    SyncPimsRequirements,
)
from unsa_audit.documents.application.ports import PimsRequirementView
from unsa_audit.documents.application.use_cases import SyncDocuments
from unsa_audit.documents.domain.documents import PIMS_KINDS, DocumentKind, DocumentLifecycle
from unsa_audit.documents.domain.pims import (
    PimsRequirement,
    RequirementState,
    evaluate_state,
    percent,
)
from unsa_audit.documents.infrastructure.content_loader import (
    DocumentContentError,
    FileDocumentSource,
    FilePimsRequirementSource,
)
from unsa_audit.seed.university_data import build_university_dataset

CONTENT = Path(__file__).resolve().parents[3] / "content"
TODAY = date(2026, 11, 11)
S = RequirementState
IN_FORCE, DRAFT = DocumentLifecycle.IN_FORCE, DocumentLifecycle.DRAFT


# ---------------------------------------------------------------------------- dominio


@pytest.mark.ac("AC-005-4")
@pytest.mark.parametrize(
    ("exists", "lifecycle", "review", "owner", "state", "issues"),
    [
        (False, None, None, None, S.MISSING, (S.MISSING,)),
        (True, DRAFT, None, "OTI", S.DRAFT, (S.DRAFT,)),
        (True, DRAFT, date(2020, 1, 1), "OTI", S.DRAFT, (S.DRAFT,)),  # un borrador no vence
        (True, DRAFT, None, None, S.DRAFT, (S.DRAFT, S.UNOWNED)),
        (True, IN_FORCE, date(2026, 11, 10), "OTI", S.EXPIRED, (S.EXPIRED,)),
        (True, IN_FORCE, date(2026, 11, 10), None, S.EXPIRED, (S.EXPIRED, S.UNOWNED)),
        (True, IN_FORCE, TODAY, "OTI", S.IN_FORCE, ()),  # vence al dia siguiente
        (True, IN_FORCE, date(2030, 1, 1), None, S.UNOWNED, (S.UNOWNED,)),
        (True, IN_FORCE, None, "", S.UNOWNED, (S.UNOWNED,)),
        (True, IN_FORCE, None, "OTI", S.IN_FORCE, ()),
    ],
)
def test_precedencia_de_estados_e_issues(exists, lifecycle, review, owner, state, issues) -> None:
    result = evaluate_state(
        exists=exists, lifecycle=lifecycle, review_date=review, owner_unit_code=owner, today=TODAY
    )
    assert (result.state, result.issues) == (state, issues)


@pytest.mark.ac("AC-005-3")
def test_porcentaje_redondeado_sin_dividir_por_cero() -> None:
    assert (percent(5, 11), percent(0, 11), percent(11, 11), percent(0, 0)) == (45, 0, 100, 0)


# ---------------------------------------------------------------------------- contenido


@pytest.fixture(scope="module")
def requirements() -> list[PimsRequirement]:
    return FilePimsRequirementSource(CONTENT).load()


@pytest.mark.ac("AC-005-1")
def test_once_requisitos_en_el_orden_del_plan(requirements) -> None:
    assert [r.clause_ref for r in requirements] == [
        "4.3", "5.2", "6.1.2", "6.1.3 e", "6.1.3 f", "6.1.3 c", "8.2", "8.3", "7.2", "9.1", "10.2",
    ]  # fmt: skip
    assert [r.sort_order for r in requirements] == list(range(1, 12))
    assert all(r.title and r.summary and r.expected_evidence for r in requirements)
    assert "  " not in requirements[0].summary, "el texto plegado de YAML se normaliza"


@pytest.mark.ac("AC-005-2")
def test_cada_requisito_tiene_un_tipo_pims_distinto_y_no_sobran_tipos(requirements) -> None:
    kinds = [r.document_kind for r in requirements]
    assert len(set(kinds)) == 11 and set(kinds) == set(PIMS_KINDS)
    assert len({r.code for r in requirements}) == 11


@pytest.mark.ac("AC-005-7")
def test_las_unidades_responsables_existen_en_el_seed(requirements) -> None:
    codes = {u.code for u in build_university_dataset().org_units}
    assert {r.responsible_unit_code for r in requirements} <= codes


@pytest.mark.ac("AC-005-7")
def test_documentos_pims_validos_y_con_un_solo_documento_por_tipo() -> None:
    seeds = [s for s in FileDocumentSource(CONTENT).load() if s.document.kind in PIMS_KINDS]
    assert len(seeds) == 10
    assert len({s.document.kind for s in seeds}) == 10
    assert {s.document.kind for s in seeds} == set(PIMS_KINDS) - {DocumentKind.PIMS_MONITORING}
    owners = {s.document.owner_unit_code for s in seeds} - {None}
    assert owners <= {u.code for u in build_university_dataset().org_units}
    assert all(s.document.code.startswith("pims-") for s in seeds)


@pytest.mark.ac("AC-005-7")
def test_contenido_pims_roto_se_rechaza(tmp_path: Path) -> None:
    (tmp_path / "pims").mkdir()
    path = tmp_path / "pims" / "requirements.yaml"
    path.write_text("requirements: []\nx: 1\n", encoding="utf-8")
    assert FilePimsRequirementSource(tmp_path).load() == []
    path.write_text("otra: cosa\n", encoding="utf-8")
    with pytest.raises(DocumentContentError, match="requirements"):
        FilePimsRequirementSource(tmp_path).load()
    path.write_text(
        "requirements:\n  - {code: a, clause_ref: '1', title: t, document_kind: NOPE,"
        " summary: s, expected_evidence: e}\n",
        encoding="utf-8",
    )
    with pytest.raises(DocumentContentError, match="requisito #1"):
        FilePimsRequirementSource(tmp_path).load()
    item = "{code: %s, clause_ref: '1', title: t, document_kind: PIMS_SCOPE, summary: s, expected_evidence: e}"
    path.write_text(f"requirements:\n  - {item % 'a'}\n  - {item % 'b'}\n", encoding="utf-8")
    with pytest.raises(DocumentContentError, match="repetidos"):
        FilePimsRequirementSource(tmp_path).load()


@pytest.mark.ac("AC-005-7")
def test_documento_con_lifecycle_o_fecha_invalidos_se_rechaza(tmp_path: Path) -> None:
    doc = tmp_path / "institutional" / "x"
    doc.mkdir(parents=True)
    (doc / "v1.md").write_text("---\nmessage: m\nauthor: a\ndate: 2025-01-01\n---\n# X\n")
    base = "code: x\nkind: PIMS_SCOPE\ntitle: X\n"
    (doc / "document.yaml").write_text(base + "lifecycle: publicado\n", encoding="utf-8")
    with pytest.raises(DocumentContentError, match="lifecycle"):
        FileDocumentSource(tmp_path).load()
    (doc / "document.yaml").write_text(base + "review_date: ayer\n", encoding="utf-8")
    with pytest.raises(DocumentContentError, match="review_date"):
        FileDocumentSource(tmp_path).load()
    (doc / "document.yaml").write_text(base, encoding="utf-8")
    assert FileDocumentSource(tmp_path).load()[0].document.lifecycle is IN_FORCE


# ---------------------------------------------------------------------------- casos de uso


class InMemoryRequirements:
    def __init__(self) -> None:
        self.items: list[PimsRequirement] = []

    async def replace_all(self, requirements: list[PimsRequirement]) -> None:
        self.items = list(requirements)

    async def list_all(self) -> list[PimsRequirementView]:
        return [PimsRequirementView(r, r.responsible_unit_code) for r in self.items]


@pytest.fixture
async def stores():
    requirements, documents = InMemoryRequirements(), InMemoryDocumentRepository()
    await SyncPimsRequirements(requirements, FilePimsRequirementSource(CONTENT)).execute()
    await SyncDocuments(documents, FileDocumentSource(CONTENT)).execute()
    return requirements, documents


@pytest.mark.ac("AC-005-1")
async def test_listar_requisitos_y_sync_reemplaza(stores) -> None:
    requirements, _ = stores
    assert len(await ListPimsRequirements(requirements).execute()) == 11
    assert (
        await SyncPimsRequirements(requirements, FilePimsRequirementSource(CONTENT)).execute() == 11
    )
    assert len(requirements.items) == 11, "reemplazo total, sin duplicar"


@pytest.mark.ac("AC-005-3")
@pytest.mark.ac("AC-005-6")
async def test_completitud_del_estado_sembrado(stores) -> None:
    requirements, documents = stores
    result = await GetPimsCompleteness(requirements, documents, today=lambda: TODAY).execute()
    assert (result.total, result.in_force, result.percent_in_force) == (11, 5, 45)
    assert result.as_of == TODAY
    assert {s.value: n for s, n in result.counts.items()} == {
        "in_force": 5, "expired": 2, "draft": 2, "unowned": 1, "missing": 1,
    }  # fmt: skip

    by_clause = {i.requirement.requirement.clause_ref: i for i in result.items}
    expected = {
        "4.3": S.IN_FORCE, "5.2": S.IN_FORCE, "6.1.2": S.EXPIRED, "6.1.3 e": S.DRAFT,
        "6.1.3 f": S.UNOWNED, "6.1.3 c": S.IN_FORCE, "8.2": S.IN_FORCE, "8.3": S.DRAFT,
        "7.2": S.IN_FORCE, "9.1": S.MISSING, "10.2": S.EXPIRED,
    }  # fmt: skip
    assert {c: i.evaluation.state for c, i in by_clause.items()} == expected
    assert by_clause["9.1"].document is None
    assert by_clause["6.1.3 f"].document is not None
    assert by_clause["6.1.3 f"].document.document.owner_unit_code is None
    assert [i.requirement.requirement.sort_order for i in result.items] == list(range(1, 12))


@pytest.mark.ac("AC-005-3")
async def test_el_estado_depende_de_la_fecha_de_referencia(stores) -> None:
    requirements, documents = stores
    future = await GetPimsCompleteness(
        requirements, documents, today=lambda: date(2031, 1, 1)
    ).execute()
    # Todo lo vigente (5 al dia + 2 ya vencidos + el sin responsable) acaba vencido.
    assert {s.value: n for s, n in future.counts.items()} == {
        "in_force": 0, "expired": 8, "draft": 2, "unowned": 0, "missing": 1,
    }  # fmt: skip
    past = await GetPimsCompleteness(
        requirements, documents, today=lambda: date(2025, 1, 1)
    ).execute()
    assert past.counts[S.EXPIRED] == 0 and past.in_force == 7
