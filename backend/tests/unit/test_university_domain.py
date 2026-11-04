from collections import Counter
from uuid import uuid4

import pytest

from unsa_audit.seed.university_data import build_university_dataset
from unsa_audit.university.domain.entities import OrgUnit, OrgUnitKind
from unsa_audit.university.domain.org_tree import build_org_tree


def _unit(name: str, parent: OrgUnit | None, kind: OrgUnitKind = OrgUnitKind.OFICINA) -> OrgUnit:
    return OrgUnit(
        id=uuid4(), parent_id=parent.id if parent else None, kind=kind, name=name, code=name
    )


@pytest.mark.ac("AC-002-11")
def test_build_org_tree_anida_y_ordena_por_nombre() -> None:
    root = _unit("Rectorado", None, OrgUnitKind.RECTORADO)
    b = _unit("B-Oficina", root)
    a = _unit("A-Oficina", root)
    a1 = _unit("A1", a)
    roots = build_org_tree([a1, b, root, a])  # desordenado a proposito
    assert len(roots) == 1
    assert [c.unit.name for c in roots[0].children] == ["A-Oficina", "B-Oficina"]
    assert roots[0].children[0].children[0].unit == a1


@pytest.mark.ac("AC-002-10")
def test_dataset_cumple_cantidades_de_la_spec() -> None:
    ds = build_university_dataset()
    kinds = Counter(u.kind for u in ds.org_units)
    assert kinds[OrgUnitKind.RECTORADO] == 1
    assert kinds[OrgUnitKind.VICERRECTORADO] == 2
    assert kinds[OrgUnitKind.FACULTAD] == 4
    assert kinds[OrgUnitKind.ESCUELA] == 12
    assert len(ds.org_units) >= 25
    assert len(ds.people) >= 60
    assert len(ds.systems) == 8
    assert len(ds.processing_activities) == 10


@pytest.mark.ac("AC-002-10")
def test_dataset_es_consistente_y_unico() -> None:
    ds = build_university_dataset()
    unit_ids = {u.id for u in ds.org_units}
    position_ids = {p.id for p in ds.positions}
    person_ids = {p.id for p in ds.people}
    system_ids = {s.id for s in ds.systems}

    assert len(unit_ids) == len(ds.org_units)
    assert len({u.code for u in ds.org_units}) == len(ds.org_units)
    assert len({p.full_name for p in ds.people}) == len(ds.people), "nombres repetidos"
    assert sum(1 for u in ds.org_units if u.parent_id is None) == 1
    assert all(u.parent_id in unit_ids for u in ds.org_units if u.parent_id)
    assert all(p.org_unit_id in unit_ids for p in ds.positions)
    assert all(
        p.reports_to_position_id in position_ids for p in ds.positions if p.reports_to_position_id
    )
    assert all(p.position_id in position_ids for p in ds.people if p.position_id)
    holders = [p.position_id for p in ds.people if p.position_id]
    assert len(holders) == len(set(holders)), "un cargo con dos titulares"
    assert all(s.owner_org_unit_id in unit_ids for s in ds.systems)
    assert all(o.system_id in system_ids and o.person_id in person_ids for o in ds.data_owners)
    assert all(a.org_unit_id in unit_ids for a in ds.processing_activities)


@pytest.mark.ac("AC-002-10")
def test_dataset_ordena_padres_antes_que_hijos() -> None:
    ds = build_university_dataset()
    seen_units: set = set()
    for u in ds.org_units:
        assert u.parent_id is None or u.parent_id in seen_units
        seen_units.add(u.id)
    seen_positions: set = set()
    for p in ds.positions:
        assert p.reports_to_position_id is None or p.reports_to_position_id in seen_positions
        seen_positions.add(p.id)
