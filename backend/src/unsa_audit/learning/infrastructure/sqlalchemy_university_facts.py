from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from unsa_audit.learning.application.ports import (
    ActivityFact,
    PositionFact,
    SystemFact,
    UnitFact,
    UniversitySnapshot,
)
from unsa_audit.university.infrastructure.models import (
    OrgUnitModel,
    PositionModel,
    ProcessingActivityModel,
    SystemModel,
)


class SqlAlchemyUniversityFacts:
    """Lee de la BD ficticia los hechos que usan los generadores de ejercicios."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    async def snapshot(self) -> UniversitySnapshot:
        async with self._sf() as session:
            units = list(await session.scalars(select(OrgUnitModel)))
            by_id = {u.id: u for u in units}
            positions = await session.scalars(select(PositionModel))
            systems = await session.scalars(select(SystemModel))
            activities = await session.scalars(select(ProcessingActivityModel))
            return UniversitySnapshot(
                units=[UnitFact(u.code, u.name, u.kind) for u in units],
                positions=[
                    PositionFact(
                        p.title,
                        by_id[p.org_unit_id].kind,
                        by_id[p.org_unit_id].code,
                        by_id[p.org_unit_id].name,
                    )
                    for p in positions
                ],
                systems=[
                    SystemFact(
                        s.name,
                        by_id[s.owner_org_unit_id].name,
                        by_id[s.owner_org_unit_id].code,
                        tuple(s.data_categories),
                    )
                    for s in systems
                ],
                activities=[
                    ActivityFact(
                        a.name,
                        by_id[a.org_unit_id].code,
                        by_id[a.org_unit_id].name,
                        a.purpose,
                        a.legal_basis,
                        tuple(a.data_categories),
                        a.retention,
                    )
                    for a in activities
                ],
            )
