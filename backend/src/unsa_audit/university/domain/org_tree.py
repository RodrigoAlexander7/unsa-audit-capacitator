from dataclasses import dataclass, field

from unsa_audit.university.domain.entities import OrgUnit


@dataclass
class OrgTreeNode:
    unit: OrgUnit
    children: list["OrgTreeNode"] = field(default_factory=list)


def build_org_tree(units: list[OrgUnit]) -> list[OrgTreeNode]:
    """Devuelve las raices (unidades sin padre) con sus hijos anidados, ordenados por nombre."""
    nodes = {unit.id: OrgTreeNode(unit) for unit in units}
    roots: list[OrgTreeNode] = []
    for node in nodes.values():
        parent = nodes.get(node.unit.parent_id) if node.unit.parent_id else None
        (parent.children if parent else roots).append(node)

    def sort_rec(items: list[OrgTreeNode]) -> None:
        items.sort(key=lambda n: n.unit.name)
        for item in items:
            sort_rec(item.children)

    sort_rec(roots)
    return roots
