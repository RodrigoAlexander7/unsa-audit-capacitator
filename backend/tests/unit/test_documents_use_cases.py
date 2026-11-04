from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from tests.unit.fakes_documents import InMemoryDocumentRepository
from unsa_audit.documents.application.errors import (
    AlreadyResolved,
    ChangeRequestNotFound,
    DocumentNotFound,
    InvalidChangeRequest,
    NoChanges,
    StaleBase,
    VersionNotFound,
)
from unsa_audit.documents.application.use_cases import (
    Decision,
    GetChangeRequest,
    GetDiff,
    GetDocument,
    GetVersion,
    ListChangeRequests,
    ListVersions,
    ProposeChange,
    ResolveChangeRequest,
    SyncDocuments,
)
from unsa_audit.documents.domain.diff import content_hash
from unsa_audit.documents.domain.documents import ChangeImpact, ChangeStatus
from unsa_audit.documents.infrastructure.content_loader import FileDocumentSource

CONTENT = Path(__file__).resolve().parents[3] / "content"
NOW = datetime(2026, 1, 1, tzinfo=UTC)
USER, ADMIN = uuid4(), uuid4()


@pytest.fixture
async def repo() -> InMemoryDocumentRepository:
    repository = InMemoryDocumentRepository()
    await SyncDocuments(repository, FileDocumentSource(CONTENT)).execute()
    return repository


async def _current_text(repo: InMemoryDocumentRepository, code: str = "rof") -> str:
    return (await GetDocument(repo).execute(code)).current.content_md


def _propose(repo):
    return ProposeChange(repo, clock=lambda: NOW)


def _resolve(repo):
    return ResolveChangeRequest(repo, clock=lambda: NOW)


async def _new_request(repo, text_suffix: str = "\nNota nueva.\n", code: str = "rof"):
    current = await _current_text(repo, code)
    return await _propose(repo).execute(
        USER, "Ana Quispe", code, "Añade una nota", "Porque sí", ChangeImpact.COSMETICO,
        current + text_suffix,
    )  # fmt: skip


@pytest.mark.ac("AC-004-2")
async def test_get_document_y_versiones(repo) -> None:
    detail = await GetDocument(repo).execute("rof")
    assert detail.summary.current_number == 3 and detail.current.number == 3
    _, versions = await ListVersions(repo).execute("rof")
    assert [v.number for v in versions] == [1, 2, 3]
    _, v2 = await GetVersion(repo).execute("rof", 2)
    assert "preside el Consejo" in v2.content_md
    with pytest.raises(DocumentNotFound):
        await GetDocument(repo).execute("nada")
    with pytest.raises(VersionNotFound):
        await GetVersion(repo).execute("rof", 9)


@pytest.mark.ac("AC-004-4")
async def test_diff_entre_versiones_por_defecto_to_menos_1(repo) -> None:
    result = await GetDiff(repo).execute("rof", to_number=2)
    assert (result.from_number, result.to_number) == (1, 2)
    assert (result.diff.additions, result.diff.deletions) == (1, 1)
    same = await GetDiff(repo).execute("rof", to_number=3, from_number=3)
    assert same.diff.hunks == []
    with pytest.raises(VersionNotFound):
        await GetDiff(repo).execute("rof", to_number=1)  # no hay v0
    with pytest.raises(DocumentNotFound):
        await GetDiff(repo).execute("nada", to_number=2)


@pytest.mark.ac("AC-004-5")
async def test_proponer_crea_solicitud_abierta_sobre_la_version_vigente(repo) -> None:
    change = await _new_request(repo)
    assert change.status is ChangeStatus.OPEN
    assert change.base_version_number == 3 and change.proposed_by == USER
    assert change.proposed_by_name == "Ana Quispe" and change.created_at == NOW
    summary = await GetDocument(repo).execute("rof")
    assert summary.summary.open_change_requests == 1


@pytest.mark.ac("AC-004-6")
@pytest.mark.parametrize(
    ("title", "rationale", "content"),
    [("  ", "x", "texto"), ("t", "  ", "texto"), ("t", "x", "   \n "), ("t" * 201, "x", "texto"),
     ("t", "x" * 5001, "texto"), ("t", "x", "y" * 200_001)],
)  # fmt: skip
async def test_propuesta_invalida(repo, title, rationale, content) -> None:
    with pytest.raises(InvalidChangeRequest):
        await _propose(repo).execute(
            USER, "Ana", "rof", title, rationale, ChangeImpact.COSMETICO, content
        )


@pytest.mark.ac("AC-004-6")
async def test_propuesta_sin_cambios_reales_se_rechaza_incluso_con_crlf_y_espacios(repo) -> None:
    current = await _current_text(repo)
    for same in (current, current.replace("\n", "\r\n"), current.replace("\n", "   \n") + "\n\n"):
        with pytest.raises(NoChanges):
            await _propose(repo).execute(USER, "Ana", "rof", "t", "r", ChangeImpact.COSMETICO, same)
    with pytest.raises(DocumentNotFound):
        await _propose(repo).execute(USER, "Ana", "nada", "t", "r", ChangeImpact.COSMETICO, "x")


@pytest.mark.ac("AC-004-7")
async def test_listar_y_detallar_solicitudes(repo) -> None:
    change = await _new_request(repo)
    other = await _new_request(repo, code="mof")
    await _resolve(repo).execute(other.id, ADMIN, "Admin", Decision.REJECT, "No procede")

    listing = ListChangeRequests(repo)
    assert {c.id for c in await listing.execute()} == {change.id, other.id}
    assert [c.id for c in await listing.execute(ChangeStatus.OPEN)] == [change.id]
    assert [c.id for c in await listing.execute(None, "mof")] == [other.id]
    with pytest.raises(DocumentNotFound):
        await listing.execute(None, "nada")

    detail = await GetChangeRequest(repo).execute(change.id)
    assert detail.diff.additions >= 1 and detail.diff.deletions == 0
    with pytest.raises(ChangeRequestNotFound):
        await GetChangeRequest(repo).execute(uuid4())


@pytest.mark.ac("AC-004-9")
async def test_aprobar_crea_la_version_siguiente_con_trazabilidad(repo) -> None:
    change = await _new_request(repo)
    resolved = await _resolve(repo).execute(change.id, ADMIN, "Admin", Decision.APPROVE, " ok ")
    assert resolved.status is ChangeStatus.APPROVED
    assert (resolved.resolved_by, resolved.resolved_by_name) == (ADMIN, "Admin")
    assert resolved.resolution_note == "ok" and resolved.resolved_at == NOW
    assert resolved.resulting_version_number == 4

    detail = await GetDocument(repo).execute("rof")
    v4, v3 = detail.current, (await GetVersion(repo).execute("rof", 3))[1]
    assert v4.number == 4 and v4.parent_version_id == v3.id
    assert v4.author_id == USER and v4.author_label == "Ana Quispe"
    assert v4.message == "Añade una nota"
    assert v4.content_hash == content_hash(change.proposed_content_md)
    assert detail.summary.open_change_requests == 0

    version_diff = await GetDiff(repo).execute("rof", 4)
    request_diff = (await GetChangeRequest(repo).execute(change.id)).diff
    assert version_diff.diff == request_diff


@pytest.mark.ac("AC-004-10")
async def test_aprobar_con_base_obsoleta_da_stale_y_la_solicitud_sigue_abierta(repo) -> None:
    first = await _new_request(repo, "\nA\n")
    second = await _new_request(repo, "\nB\n")
    await _resolve(repo).execute(first.id, ADMIN, "Admin", Decision.APPROVE, "")
    with pytest.raises(StaleBase):
        await _resolve(repo).execute(second.id, ADMIN, "Admin", Decision.APPROVE, "")
    assert (await repo.get_change_request(second.id)).status is ChangeStatus.OPEN  # type: ignore[union-attr]
    assert (await GetDocument(repo).execute("rof")).current.number == 4
    await _resolve(repo).execute(second.id, ADMIN, "Admin", Decision.REJECT, "obsoleta")


@pytest.mark.ac("AC-004-11")
async def test_rechazar_no_crea_version_y_no_se_puede_resolver_dos_veces(repo) -> None:
    change = await _new_request(repo)
    rejected = await _resolve(repo).execute(
        change.id, ADMIN, "Admin", Decision.REJECT, "No procede"
    )
    assert rejected.status is ChangeStatus.REJECTED and rejected.resolution_note == "No procede"
    assert rejected.resulting_version_id is None
    assert (await GetDocument(repo).execute("rof")).current.number == 3
    for decision in (Decision.APPROVE, Decision.REJECT):
        with pytest.raises(AlreadyResolved):
            await _resolve(repo).execute(change.id, ADMIN, "Admin", decision, "")
    with pytest.raises(ChangeRequestNotFound):
        await _resolve(repo).execute(uuid4(), ADMIN, "Admin", Decision.REJECT, "")
    other = await _new_request(repo)
    with pytest.raises(InvalidChangeRequest):
        await _resolve(repo).execute(other.id, ADMIN, "Admin", Decision.REJECT, "n" * 2001)


@pytest.mark.ac("AC-004-14")
async def test_sync_no_pisa_lo_existente_y_reset_restaura(repo) -> None:
    change = await _new_request(repo)
    await _resolve(repo).execute(change.id, ADMIN, "Admin", Decision.APPROVE, "")
    assert (await GetDocument(repo).execute("rof")).current.number == 4

    created, skipped = await SyncDocuments(repo, FileDocumentSource(CONTENT)).execute()
    assert (created, skipped) == (0, 5)
    assert (await GetDocument(repo).execute("rof")).current.number == 4

    created, skipped = await SyncDocuments(repo, FileDocumentSource(CONTENT)).execute(reset=True)
    assert (created, skipped) == (5, 0)
    assert (await GetDocument(repo).execute("rof")).current.number == 3
    assert await repo.list_change_requests() == []
