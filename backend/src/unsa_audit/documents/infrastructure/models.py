import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from unsa_audit.core.database import Base


class DocumentModel(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True)
    kind: Mapped[str] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(String(200))
    owner_unit_code: Mapped[str | None] = mapped_column(String(30))
    lifecycle: Mapped[str] = mapped_column(String(20), server_default="in_force")
    review_date: Mapped[date | None] = mapped_column(Date)
    # FK circular con document_versions: se crea despues (use_alter).
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("document_versions.id", use_alter=True, name="fk_documents_current_version")
    )


class DocumentVersionModel(Base):
    __tablename__ = "document_versions"
    __table_args__ = (UniqueConstraint("document_id", "number"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    number: Mapped[int] = mapped_column(Integer)
    content_md: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64))
    parent_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("document_versions.id", ondelete="SET NULL")
    )
    author_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    author_label: Mapped[str] = mapped_column(String(160))
    message: Mapped[str] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ChangeRequestModel(Base):
    __tablename__ = "change_requests"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    document_code: Mapped[str] = mapped_column(String(60))
    title: Mapped[str] = mapped_column(String(200))
    rationale: Mapped[str] = mapped_column(Text)
    impact: Mapped[str] = mapped_column(String(20))
    proposed_content_md: Mapped[str] = mapped_column(Text)
    base_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_versions.id", ondelete="CASCADE")
    )
    base_version_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), index=True)
    proposed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    proposed_by_name: Mapped[str] = mapped_column(String(160))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    resolved_by_name: Mapped[str | None] = mapped_column(String(160))
    resolution_note: Mapped[str | None] = mapped_column(Text)
    resulting_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("document_versions.id", ondelete="SET NULL")
    )
    resulting_version_number: Mapped[int | None] = mapped_column(Integer)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PimsRequirementModel(Base):
    __tablename__ = "pims_requirements"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True)
    clause_ref: Mapped[str] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(String(200))
    document_kind: Mapped[str] = mapped_column(String(30), unique=True)
    summary: Mapped[str] = mapped_column(Text)
    expected_evidence: Mapped[str] = mapped_column(Text)
    responsible_unit_code: Mapped[str | None] = mapped_column(String(30))
    sort_order: Mapped[int] = mapped_column(Integer, unique=True)
