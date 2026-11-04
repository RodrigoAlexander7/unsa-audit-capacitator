from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from unsa_audit.university.domain.entities import DataOwnerRole, OrgUnit, Person, System


@dataclass(frozen=True)
class PositionView:
    id: UUID
    title: str
    reports_to_title: str | None
    holder: Person | None


@dataclass(frozen=True)
class OrgUnitDetail:
    unit: OrgUnit
    parent: OrgUnit | None
    children: list[OrgUnit]
    positions: list[PositionView]


@dataclass(frozen=True)
class DataOwnerView:
    person: Person
    role: DataOwnerRole


@dataclass(frozen=True)
class SystemView:
    system: System
    owner_unit: OrgUnit
    owners: list[DataOwnerView]


class UniversityReadRepository(Protocol):
    async def list_org_units(self) -> list[OrgUnit]: ...

    async def get_org_unit_detail(self, unit_id: UUID) -> OrgUnitDetail | None: ...

    async def list_systems(self) -> list[SystemView]: ...
