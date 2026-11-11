"""Lee `content/institutional/<codigo>/` (document.yaml + vN.md) y arma los documentos iniciales.

document.yaml   code, kind, title, owner_unit
vN.md           frontmatter (message, author, date) + contenido Markdown de la version N
"""

import re
from datetime import UTC, date, datetime, time
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

import yaml

from unsa_audit.documents.application.ports import SeedDocument
from unsa_audit.documents.domain.diff import content_hash, normalize_content
from unsa_audit.documents.domain.documents import (
    PIMS_KINDS,
    Document,
    DocumentKind,
    DocumentLifecycle,
    DocumentVersion,
)
from unsa_audit.documents.domain.pims import PimsRequirement

_NS = uuid5(NAMESPACE_URL, "https://unsa-audit-poc.example/documents")
_VERSION_FILE = re.compile(r"^v(?P<number>\d+)\.md$")
_FRONTMATTER = re.compile(r"\A---\n(?P<meta>.*?)\n---\n(?P<body>.*)\Z", re.DOTALL)


class DocumentContentError(ValueError):
    """El contenido institucional del repositorio esta mal formado."""


def document_id(code: str) -> UUID:
    return uuid5(_NS, f"document:{code}")


def version_id(code: str, number: int) -> UUID:
    return uuid5(_NS, f"document:{code}:v{number}")


def _load_document(directory: Path) -> SeedDocument:
    meta = yaml.safe_load((directory / "document.yaml").read_text(encoding="utf-8")) or {}
    try:
        code = str(meta["code"])
        kind = DocumentKind(meta["kind"])
        title = str(meta["title"])
    except (KeyError, ValueError) as exc:
        raise DocumentContentError(f"{directory}/document.yaml: {exc}") from exc
    if code != directory.name:
        raise DocumentContentError(
            f"{directory}: `code` debe coincidir con el nombre de la carpeta"
        )

    files = {
        int(m["number"]): p for p in directory.glob("v*.md") if (m := _VERSION_FILE.match(p.name))
    }
    if not files or sorted(files) != list(range(1, len(files) + 1)):
        raise DocumentContentError(f"{directory}: las versiones deben ser v1.md..vN.md contiguas")

    doc_id = document_id(code)
    versions: list[DocumentVersion] = []
    for number in sorted(files):
        parsed = _FRONTMATTER.match(files[number].read_text(encoding="utf-8"))
        if parsed is None:
            raise DocumentContentError(f"{files[number]}: falta el frontmatter YAML")
        header = yaml.safe_load(parsed["meta"]) or {}
        if not header.get("message") or not header.get("author") or not header.get("date"):
            raise DocumentContentError(f"{files[number]}: faltan message, author o date")
        raw_date = header["date"]
        day = raw_date if isinstance(raw_date, date) else date.fromisoformat(str(raw_date))
        content = normalize_content(parsed["body"])
        versions.append(
            DocumentVersion(
                id=version_id(code, number),
                document_id=doc_id,
                number=number,
                content_md=content,
                content_hash=content_hash(content),
                parent_version_id=version_id(code, number - 1) if number > 1 else None,
                author_id=None,
                author_label=str(header["author"]),
                message=str(header["message"]),
                created_at=datetime.combine(day, time(9, 0), tzinfo=UTC),
            )
        )
    try:
        lifecycle = DocumentLifecycle(meta.get("lifecycle", "in_force"))
    except ValueError as exc:
        raise DocumentContentError(f"{directory}/document.yaml: lifecycle invalido") from exc
    raw_review = meta.get("review_date")
    try:
        review_date = (
            None
            if raw_review is None
            else raw_review
            if isinstance(raw_review, date)
            else date.fromisoformat(str(raw_review))
        )
    except ValueError as exc:
        raise DocumentContentError(f"{directory}/document.yaml: review_date invalida") from exc
    document = Document(
        id=doc_id,
        code=code,
        kind=kind,
        title=title,
        owner_unit_code=meta.get("owner_unit"),
        current_version_id=versions[-1].id,
        lifecycle=lifecycle,
        review_date=review_date,
    )
    return SeedDocument(document, versions)


class FileDocumentSource:
    def __init__(self, content_dir: Path) -> None:
        self._dir = content_dir / "institutional"

    def load(self) -> list[SeedDocument]:
        if not self._dir.exists():
            return []
        directories = sorted(
            p for p in self._dir.iterdir() if p.is_dir() and (p / "document.yaml").exists()
        )
        documents = [_load_document(p) for p in directories]
        codes = [d.document.code for d in documents]
        if len(set(codes)) != len(codes):
            raise DocumentContentError("codigos de documento repetidos")
        pims_kinds = [d.document.kind for d in documents if d.document.kind in PIMS_KINDS]
        if len(set(pims_kinds)) != len(pims_kinds):
            raise DocumentContentError("hay mas de un documento para un mismo tipo PIMS")
        return documents


def requirement_id(code: str) -> UUID:
    return uuid5(_NS, f"pims-requirement:{code}")


class FilePimsRequirementSource:
    """Lee `content/pims/requirements.yaml`: lista ordenada de los requisitos del PIMS."""

    def __init__(self, content_dir: Path) -> None:
        self._path = content_dir / "pims" / "requirements.yaml"

    def load(self) -> list[PimsRequirement]:
        if not self._path.exists():
            return []
        raw = yaml.safe_load(self._path.read_text(encoding="utf-8")) or {}
        items = raw.get("requirements")
        if not isinstance(items, list):
            raise DocumentContentError(f"{self._path}: falta la lista `requirements`")
        requirements: list[PimsRequirement] = []
        for order, item in enumerate(items, start=1):
            try:
                requirements.append(
                    PimsRequirement(
                        id=requirement_id(item["code"]),
                        code=item["code"],
                        clause_ref=str(item["clause_ref"]),
                        title=item["title"],
                        document_kind=DocumentKind(item["document_kind"]),
                        summary=" ".join(str(item["summary"]).split()),
                        expected_evidence=" ".join(str(item["expected_evidence"]).split()),
                        responsible_unit_code=item.get("responsible_unit"),
                        sort_order=order,
                    )
                )
            except (KeyError, ValueError) as exc:
                raise DocumentContentError(f"{self._path}: requisito #{order}: {exc}") from exc
        codes = [r.code for r in requirements]
        kinds = [r.document_kind for r in requirements]
        if len(set(codes)) != len(codes) or len(set(kinds)) != len(kinds):
            raise DocumentContentError(f"{self._path}: codigos o tipos de documento repetidos")
        return requirements
