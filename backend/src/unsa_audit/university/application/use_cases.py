from uuid import UUID

from unsa_audit.university.application.ports import (
    OrgUnitDetail,
    SystemView,
    UniversityReadRepository,
)
from unsa_audit.university.domain.org_tree import OrgTreeNode, build_org_tree


class OrgChartNotLoaded(Exception):
    """No hay unidades cargadas (falta ejecutar el seed)."""


class OrgUnitNotFound(Exception):
    pass


class GetOrgTree:
    def __init__(self, repo: UniversityReadRepository) -> None:
        self._repo = repo

    async def execute(self) -> OrgTreeNode:
        roots = build_org_tree(await self._repo.list_org_units())
        if not roots:
            raise OrgChartNotLoaded
        return roots[0]


class GetOrgUnitDetail:
    def __init__(self, repo: UniversityReadRepository) -> None:
        self._repo = repo

    async def execute(self, unit_id: UUID) -> OrgUnitDetail:
        detail = await self._repo.get_org_unit_detail(unit_id)
        if detail is None:
            raise OrgUnitNotFound
        return detail


class ListSystems:
    def __init__(self, repo: UniversityReadRepository) -> None:
        self._repo = repo

    async def execute(self) -> list[SystemView]:
        return await self._repo.list_systems()
