import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from unsa_audit.core.database import Base


class OrgUnitModel(Base):
    __tablename__ = "org_units"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("org_units.id"), index=True)
    kind: Mapped[str] = mapped_column(String(30))
    name: Mapped[str] = mapped_column(String(160))
    code: Mapped[str] = mapped_column(String(30), unique=True)


class PositionModel(Base):
    __tablename__ = "positions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    org_unit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("org_units.id"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    reports_to_position_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("positions.id"))


class PersonModel(Base):
    __tablename__ = "people"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(160))
    kind: Mapped[str] = mapped_column(String(30))
    # Una persona ocupa a lo sumo un cargo y un cargo tiene a lo sumo un titular.
    position_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("positions.id"), unique=True)


class SystemModel(Base):
    __tablename__ = "systems"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    description: Mapped[str] = mapped_column(Text)
    owner_org_unit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("org_units.id"), index=True)
    data_categories: Mapped[list[str]] = mapped_column(ARRAY(String(80)))


class DataOwnerModel(Base):
    __tablename__ = "data_owners"

    system_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("systems.id"), primary_key=True)
    person_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("people.id"), primary_key=True)
    role: Mapped[str] = mapped_column(String(20), primary_key=True)


class ProcessingActivityModel(Base):
    __tablename__ = "processing_activities"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    org_unit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("org_units.id"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    purpose: Mapped[str] = mapped_column(Text)
    legal_basis: Mapped[str] = mapped_column(String(160))
    data_categories: Mapped[list[str]] = mapped_column(ARRAY(String(80)))
    retention: Mapped[str] = mapped_column(String(160))
