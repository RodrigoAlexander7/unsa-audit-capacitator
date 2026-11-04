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
from unsa_audit.documents.domain.documents import Document, DocumentKind, DocumentVersion

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
    document = Document(
        id=doc_id,
        code=code,
        kind=kind,
        title=title,
        owner_unit_code=meta.get("owner_unit"),
        current_version_id=versions[-1].id,
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
        return documents
