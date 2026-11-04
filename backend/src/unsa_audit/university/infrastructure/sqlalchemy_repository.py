from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from unsa_audit.university.application.ports import (
    DataOwnerView,
    OrgUnitDetail,
    PositionView,
    SystemView,
)
from unsa_audit.university.domain.entities import (
    DataOwnerRole,
    OrgUnit,
    OrgUnitKind,
    Person,
    PersonKind,
    System,
)
from unsa_audit.university.infrastructure.models import (
    DataOwnerModel,
    OrgUnitModel,
    PersonModel,
    PositionModel,
    SystemModel,
)


def _unit(m: OrgUnitModel) -> OrgUnit:
    return OrgUnit(
        id=m.id, parent_id=m.parent_id, kind=OrgUnitKind(m.kind), name=m.name, code=m.code
    )


def _person(m: PersonModel) -> Person:
    return Person(
        id=m.id, full_name=m.full_name, kind=PersonKind(m.kind), position_id=m.position_id
    )


class SqlAlchemyUniversityReadRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def list_org_units(self) -> list[OrgUnit]:
        async with self._session_factory() as session:
            rows = await session.scalars(select(OrgUnitModel))
            return [_unit(m) for m in rows]

    async def get_org_unit_detail(self, unit_id: UUID) -> OrgUnitDetail | None:
        async with self._session_factory() as session:
            unit_m = await session.get(OrgUnitModel, unit_id)
            if unit_m is None:
                return None
            parent_m = (
                await session.get(OrgUnitModel, unit_m.parent_id) if unit_m.parent_id else None
            )
            children = await session.scalars(
                select(OrgUnitModel)
                .where(OrgUnitModel.parent_id == unit_id)
                .order_by(OrgUnitModel.name)
            )
            positions = (
                await session.scalars(
                    select(PositionModel)
                    .where(PositionModel.org_unit_id == unit_id)
                    .order_by(PositionModel.title)
                )
            ).all()
            holders = {
                p.position_id: p
                for p in await session.scalars(
                    select(PersonModel).where(
                        PersonModel.position_id.in_([p.id for p in positions])
                    )
                )
            }
            boss_ids = {p.reports_to_position_id for p in positions if p.reports_to_position_id}
            boss_titles = {
                b.id: b.title
                for b in await session.scalars(
                    select(PositionModel).where(PositionModel.id.in_(boss_ids))
                )
            }
            return OrgUnitDetail(
                unit=_unit(unit_m),
                parent=_unit(parent_m) if parent_m else None,
                children=[_unit(c) for c in children],
                positions=[
                    PositionView(
                        id=p.id,
                        title=p.title,
                        reports_to_title=boss_titles.get(p.reports_to_position_id)
                        if p.reports_to_position_id
                        else None,
                        holder=_person(holders[p.id]) if p.id in holders else None,
                    )
                    for p in positions
                ],
            )

    async def list_systems(self) -> list[SystemView]:
        async with self._session_factory() as session:
            systems = (await session.scalars(select(SystemModel).order_by(SystemModel.name))).all()
            units = {u.id: u for u in await session.scalars(select(OrgUnitModel))}
            owner_rows = await session.execute(
                select(DataOwnerModel, PersonModel).join(
                    PersonModel, PersonModel.id == DataOwnerModel.person_id
                )
            )
            owners: dict[UUID, list[DataOwnerView]] = {}
            for owner, person in owner_rows:
                owners.setdefault(owner.system_id, []).append(
                    DataOwnerView(person=_person(person), role=DataOwnerRole(owner.role))
                )
            return [
                SystemView(
                    system=System(
                        id=s.id,
                        name=s.name,
                        description=s.description,
                        owner_org_unit_id=s.owner_org_unit_id,
                        data_categories=tuple(s.data_categories),
                    ),
                    owner_unit=_unit(units[s.owner_org_unit_id]),
                    owners=sorted(owners.get(s.id, []), key=lambda o: o.role.value),
                )
                for s in systems
            ]
