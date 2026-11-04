"""AC-004-13: el contenido institucional del repositorio es valido y coherente."""

import hashlib
from pathlib import Path

import pytest

from unsa_audit.documents.domain.diff import compute_diff
from unsa_audit.documents.domain.documents import PIMS_KINDS, DocumentKind
from unsa_audit.documents.infrastructure.content_loader import (
    DocumentContentError,
    FileDocumentSource,
)
from unsa_audit.seed.university_data import build_university_dataset

CONTENT = Path(__file__).resolve().parents[3] / "content"


@pytest.fixture(scope="module")
def seeds():
    return {s.document.code: s for s in FileDocumentSource(CONTENT).load()}


@pytest.mark.ac("AC-004-13")
def test_cinco_documentos_con_el_historial_esperado(seeds) -> None:
    general = {c: s for c, s in seeds.items() if not c.startswith("pims-")}
    assert {c: len(s.versions) for c, s in general.items()} == {
        "rof": 3, "mof": 2, "reglamento-evaluacion": 2, "estatuto": 1, "cuadro-asignacion": 1,
    }  # fmt: skip
    assert {s.document.kind for s in general.values()} == set(DocumentKind) - set(PIMS_KINDS)


@pytest.mark.ac("AC-004-13")
def test_las_unidades_responsables_existen_en_el_seed_de_la_universidad(seeds) -> None:
    codes = {u.code for u in build_university_dataset().org_units}
    # El plan de tratamiento PIMS no tiene responsable a proposito (hallazgo sembrado).
    owners = {s.document.owner_unit_code for s in seeds.values()} - {None}
    assert owners <= codes, owners - codes


@pytest.mark.ac("AC-004-12")
def test_cadena_de_versiones_y_hashes_son_consistentes(seeds) -> None:
    for seed in seeds.values():
        versions = sorted(seed.versions, key=lambda v: v.number)
        assert [v.number for v in versions] == list(range(1, len(versions) + 1))
        assert versions[0].parent_version_id is None
        for previous, current in zip(versions, versions[1:], strict=False):
            assert current.parent_version_id == previous.id
            assert current.created_at > previous.created_at
        for v in versions:
            assert v.content_hash == hashlib.sha256(v.content_md.encode()).hexdigest()
            assert v.content_md.startswith("# ") and v.content_md.endswith("\n")
        assert seed.document.current_version_id == versions[-1].id


def _only_change(seeds, code: str, from_n: int, to_n: int):
    versions = {v.number: v for v in seeds[code].versions}
    return compute_diff(versions[from_n].content_md, versions[to_n].content_md)


@pytest.mark.ac("AC-004-13")
def test_los_cambios_sembrados_son_los_que_ensena_la_ruta_1(seeds) -> None:
    errata = _only_change(seeds, "rof", 1, 2)
    assert (errata.additions, errata.deletions) == (1, 1)
    old, new = (line.text for line in errata.hunks[0].lines if line.kind in ("del", "add"))
    assert "prescide" in old and "preside" in new

    dpo_in_rof = _only_change(seeds, "rof", 2, 3)
    assert dpo_in_rof.deletions == 0 and dpo_in_rof.additions == 2  # artículo 6-A + línea en blanco
    assert any("Protección de Datos Personales" in line.text for line in dpo_in_rof.hunks[0].lines)

    dpo_in_mof = _only_change(seeds, "mof", 1, 2)
    assert dpo_in_mof.additions == 1 and dpo_in_mof.deletions == 0

    plazo = _only_change(seeds, "reglamento-evaluacion", 1, 2)
    assert (plazo.additions, plazo.deletions) == (1, 1)
    texts = " ".join(line.text for line in plazo.hunks[0].lines if line.kind != "ctx")
    assert "10 días" in texts and "5 días" in texts


@pytest.mark.ac("AC-004-13")
def test_contenido_roto_se_rechaza(tmp_path: Path) -> None:
    doc = tmp_path / "institutional" / "x"
    doc.mkdir(parents=True)
    (doc / "document.yaml").write_text("code: x\nkind: ROF\ntitle: X\n", encoding="utf-8")
    (doc / "v2.md").write_text("---\nmessage: m\nauthor: a\ndate: 2025-01-01\n---\n# X\n")
    with pytest.raises(DocumentContentError, match="contiguas"):
        FileDocumentSource(tmp_path).load()

    (doc / "v2.md").rename(doc / "v1.md")
    (doc / "v1.md").write_text("sin frontmatter", encoding="utf-8")
    with pytest.raises(DocumentContentError, match="frontmatter"):
        FileDocumentSource(tmp_path).load()

    (doc / "v1.md").write_text("---\nmessage: m\n---\n# X\n", encoding="utf-8")
    with pytest.raises(DocumentContentError, match="faltan"):
        FileDocumentSource(tmp_path).load()

    (doc / "document.yaml").write_text("code: otro\nkind: ROF\ntitle: X\n", encoding="utf-8")
    with pytest.raises(DocumentContentError, match="coincidir"):
        FileDocumentSource(tmp_path).load()

    (doc / "document.yaml").write_text("code: x\nkind: NOPE\ntitle: X\n", encoding="utf-8")
    with pytest.raises(DocumentContentError):
        FileDocumentSource(tmp_path).load()
