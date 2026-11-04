from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

MAX_CONTENT_CHARS = 200_000
MAX_TITLE_CHARS = 200
MAX_RATIONALE_CHARS = 5_000
MAX_NOTE_CHARS = 2_000


class DocumentKind(StrEnum):
    # Documentos institucionales generales
    ROF = "ROF"
    MOF = "MOF"
    ESTATUTO = "ESTATUTO"
    CUADRO_ASIGNACION = "CUADRO_ASIGNACION"
    REGLAMENTO = "REGLAMENTO"
    # Conjunto documental del PIMS (ISO/IEC 27701): un tipo por requisito
    PIMS_SCOPE = "PIMS_SCOPE"
    PIMS_PRIVACY_POLICY = "PIMS_PRIVACY_POLICY"
    PIMS_RISK_PROCESS = "PIMS_RISK_PROCESS"
    PIMS_SOA = "PIMS_SOA"
    PIMS_TREATMENT_PLAN = "PIMS_TREATMENT_PLAN"
    PIMS_SECURITY_PROGRAM = "PIMS_SECURITY_PROGRAM"
    PIMS_RISK_RESULTS = "PIMS_RISK_RESULTS"
    PIMS_TREATMENT_RESULTS = "PIMS_TREATMENT_RESULTS"
    PIMS_COMPETENCE = "PIMS_COMPETENCE"
    PIMS_MONITORING = "PIMS_MONITORING"
    PIMS_NONCONFORMITIES = "PIMS_NONCONFORMITIES"


PIMS_KINDS: tuple[DocumentKind, ...] = tuple(k for k in DocumentKind if k.value.startswith("PIMS_"))


class DocumentLifecycle(StrEnum):
    IN_FORCE = "in_force"
    DRAFT = "draft"


class ChangeImpact(StrEnum):
    COSMETICO = "cosmetico"
    PROCEDIMENTAL = "procedimental"
    ESTRUCTURAL = "estructural"


class ChangeStatus(StrEnum):
    OPEN = "open"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True)
class Document:
    id: UUID
    code: str
    kind: DocumentKind
    title: str
    owner_unit_code: str | None
    current_version_id: UUID | None
    lifecycle: DocumentLifecycle = DocumentLifecycle.IN_FORCE
    review_date: date | None = None


@dataclass(frozen=True)
class DocumentVersion:
    """Version inmutable de un documento (contenido normalizado + hash)."""

    id: UUID
    document_id: UUID
    number: int
    content_md: str
    content_hash: str
    parent_version_id: UUID | None
    author_id: UUID | None
    author_label: str
    message: str
    created_at: datetime


@dataclass(frozen=True)
class ChangeRequest:
    id: UUID
    document_id: UUID
    document_code: str
    title: str
    rationale: str
    impact: ChangeImpact
    proposed_content_md: str
    base_version_id: UUID
    base_version_number: int
    status: ChangeStatus
    proposed_by: UUID | None
    proposed_by_name: str
    created_at: datetime
    resolved_by: UUID | None = None
    resolved_by_name: str | None = None
    resolution_note: str | None = None
    resulting_version_id: UUID | None = None
    resulting_version_number: int | None = None
    resolved_at: datetime | None = None
