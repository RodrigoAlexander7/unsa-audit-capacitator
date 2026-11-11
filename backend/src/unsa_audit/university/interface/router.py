from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from unsa_audit.identity.interface.dependencies import CurrentUser
from unsa_audit.university.application.ports import OrgUnitDetail, SystemView
from unsa_audit.university.application.use_cases import OrgChartNotLoaded, OrgUnitNotFound
from unsa_audit.university.domain.entities import OrgUnit, Person
from unsa_audit.university.domain.org_tree import OrgTreeNode

router = APIRouter(tags=["university"])


class OrgUnitSummary(BaseModel):
    id: str
    kind: str
    name: str
    code: str

    @classmethod
    def from_domain(cls, unit: OrgUnit) -> "OrgUnitSummary":
        return cls(id=str(unit.id), kind=unit.kind.value, name=unit.name, code=unit.code)


class OrgTreeResponse(OrgUnitSummary):
    children: list["OrgTreeResponse"]

    @classmethod
    def from_node(cls, node: OrgTreeNode) -> "OrgTreeResponse":
        return cls(
            id=str(node.unit.id),
            kind=node.unit.kind.value,
            name=node.unit.name,
            code=node.unit.code,
            children=[cls.from_node(c) for c in node.children],
        )


class PersonResponse(BaseModel):
    id: str
    full_name: str
    kind: str

    @classmethod
    def from_domain(cls, person: Person) -> "PersonResponse":
        return cls(id=str(person.id), full_name=person.full_name, kind=person.kind.value)


class PositionResponse(BaseModel):
    id: str
    title: str
    reports_to_title: str | None
    holder: PersonResponse | None


class OrgUnitDetailResponse(BaseModel):
    unit: OrgUnitSummary
    parent: OrgUnitSummary | None
    children: list[OrgUnitSummary]
    positions: list[PositionResponse]

    @classmethod
    def from_domain(cls, detail: OrgUnitDetail) -> "OrgUnitDetailResponse":
        return cls(
            unit=OrgUnitSummary.from_domain(detail.unit),
            parent=OrgUnitSummary.from_domain(detail.parent) if detail.parent else None,
            children=[OrgUnitSummary.from_domain(c) for c in detail.children],
            positions=[
                PositionResponse(
                    id=str(p.id),
                    title=p.title,
                    reports_to_title=p.reports_to_title,
                    holder=PersonResponse.from_domain(p.holder) if p.holder else None,
                )
                for p in detail.positions
            ],
        )


class DataOwnerResponse(BaseModel):
    person: PersonResponse
    role: str


class SystemResponse(BaseModel):
    id: str
    name: str
    description: str
    owner_unit: OrgUnitSummary
    data_categories: list[str]
    owners: list[DataOwnerResponse]

    @classmethod
    def from_domain(cls, view: SystemView) -> "SystemResponse":
        return cls(
            id=str(view.system.id),
            name=view.system.name,
            description=view.system.description,
            owner_unit=OrgUnitSummary.from_domain(view.owner_unit),
            data_categories=list(view.system.data_categories),
            owners=[
                DataOwnerResponse(person=PersonResponse.from_domain(o.person), role=o.role.value)
                for o in view.owners
            ],
        )


@router.get("/org-units", response_model=OrgTreeResponse)
async def org_units(_: CurrentUser, request: Request) -> OrgTreeResponse:
    try:
        root = await request.app.state.get_org_tree.execute()
    except OrgChartNotLoaded as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Organigrama no cargado") from exc
    return OrgTreeResponse.from_node(root)


@router.get("/org-units/{unit_id}", response_model=OrgUnitDetailResponse)
async def org_unit_detail(unit_id: UUID, _: CurrentUser, request: Request) -> OrgUnitDetailResponse:
    try:
        detail = await request.app.state.get_org_unit_detail.execute(unit_id)
    except OrgUnitNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unidad no encontrada") from exc
    return OrgUnitDetailResponse.from_domain(detail)


@router.get("/systems", response_model=list[SystemResponse])
async def systems(_: CurrentUser, request: Request) -> list[SystemResponse]:
    views = await request.app.state.list_systems.execute()
    return [SystemResponse.from_domain(v) for v in views]
