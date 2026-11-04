"""Entidades de la UNSA ficticia (POC). Todos los datos son inventados."""

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class OrgUnitKind(StrEnum):
    RECTORADO = "rectorado"
    VICERRECTORADO = "vicerrectorado"
    FACULTAD = "facultad"
    ESCUELA = "escuela"
    OFICINA = "oficina"


class PersonKind(StrEnum):
    ESTUDIANTE = "estudiante"
    DOCENTE = "docente"
    ADMINISTRATIVO = "administrativo"


class DataOwnerRole(StrEnum):
    CONTROLLER = "controller"
    PROCESSOR = "processor"
    STEWARD = "steward"


@dataclass(frozen=True)
class OrgUnit:
    id: UUID
    parent_id: UUID | None
    kind: OrgUnitKind
    name: str
    code: str


@dataclass(frozen=True)
class Position:
    id: UUID
    org_unit_id: UUID
    title: str
    reports_to_position_id: UUID | None


@dataclass(frozen=True)
class Person:
    id: UUID
    full_name: str
    kind: PersonKind
    position_id: UUID | None


@dataclass(frozen=True)
class System:
    id: UUID
    name: str
    description: str
    owner_org_unit_id: UUID
    data_categories: tuple[str, ...]


@dataclass(frozen=True)
class DataOwner:
    system_id: UUID
    person_id: UUID
    role: DataOwnerRole


@dataclass(frozen=True)
class ProcessingActivity:
    id: UUID
    org_unit_id: UUID
    name: str
    purpose: str
    legal_basis: str
    data_categories: tuple[str, ...]
    retention: str
