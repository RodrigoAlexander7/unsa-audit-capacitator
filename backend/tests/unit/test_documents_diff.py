import hashlib

import pytest

from unsa_audit.documents.domain.diff import compute_diff, content_hash, normalize_content


@pytest.mark.ac("AC-004-12")
def test_normalizacion_unifica_saltos_espacios_finales_y_salto_final() -> None:
    assert normalize_content("a  \r\nb\t\r\n\r\n\r\n") == "a\nb\n"
    assert normalize_content("a\rb") == "a\nb\n"
    assert normalize_content("") == ""
    assert normalize_content("\n\n") == ""
    assert normalize_content("x") == "x\n"
    assert normalize_content("\n\n  a\nb\n") == "  a\nb\n"


@pytest.mark.ac("AC-004-12")
def test_hash_es_sha256_del_contenido_normalizado() -> None:
    expected = hashlib.sha256(b"hola\nmundo\n").hexdigest()
    assert content_hash("hola  \r\nmundo") == expected
    assert content_hash("hola\nmundo\n\n\n") == expected
    assert content_hash("hola\nmundo!") != expected


@pytest.mark.ac("AC-004-6")
def test_cambios_solo_de_formato_no_son_cambios() -> None:
    a, b = "linea 1\nlinea 2\n", "linea 1  \r\nlinea 2\r\n\r\n"
    assert content_hash(a) == content_hash(b)
    diff = compute_diff(a, b)
    assert (diff.additions, diff.deletions, diff.hunks) == (0, 0, [])


@pytest.mark.ac("AC-004-4")
def test_diff_reemplazo_de_una_linea_con_contexto_y_numeracion() -> None:
    old = "uno\ndos\ntres\ncuatro\ncinco\n"
    new = "uno\ndos\nTRES\ncuatro\ncinco\n"
    diff = compute_diff(old, new)
    assert (diff.additions, diff.deletions) == (1, 1)
    assert len(diff.hunks) == 1
    lines = [(line.kind, line.old_line, line.new_line, line.text) for line in diff.hunks[0].lines]
    assert lines == [
        ("ctx", 1, 1, "uno"),
        ("ctx", 2, 2, "dos"),
        ("del", 3, None, "tres"),
        ("add", None, 3, "TRES"),
        ("ctx", 4, 4, "cuatro"),
        ("ctx", 5, 5, "cinco"),
    ]
    assert (diff.hunks[0].old_start, diff.hunks[0].new_start) == (1, 1)


@pytest.mark.ac("AC-004-4")
def test_diff_inserciones_y_eliminaciones_y_hunks_separados() -> None:
    old = "\n".join(f"l{i}" for i in range(1, 21)) + "\n"
    new_lines = [f"l{i}" for i in range(1, 21)]
    new_lines.insert(2, "NUEVA")  # inserta cerca del inicio
    del new_lines[-3]  # elimina cerca del final
    diff = compute_diff(old, "\n".join(new_lines) + "\n")
    assert (diff.additions, diff.deletions) == (1, 1)
    assert len(diff.hunks) == 2, "cambios lejanos van en hunks distintos"
    kinds = [line.kind for line in diff.hunks[0].lines]
    assert kinds.count("add") == 1 and kinds.count("del") == 0


@pytest.mark.ac("AC-004-4")
def test_diff_invertido_intercambia_adiciones_y_eliminaciones() -> None:
    forward = compute_diff("a\nb\n", "a\nc\nd\n")
    backward = compute_diff("a\nc\nd\n", "a\nb\n")
    assert (forward.additions, forward.deletions) == (backward.deletions, backward.additions)


@pytest.mark.ac("AC-004-4")
def test_diff_de_documento_nuevo_o_vaciado() -> None:
    assert compute_diff("", "a\nb\n").additions == 2
    assert compute_diff("a\nb\n", "").deletions == 2
