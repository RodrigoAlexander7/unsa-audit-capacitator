"""Generadores de ejercicios desde los hechos de la UNSA ficticia (puros, deterministas)."""

from collections.abc import Callable
from typing import Any

from unsa_audit.learning.application.ports import UniversitySnapshot
from unsa_audit.learning.domain.exercises import InvalidExerciseSpec, Spec

KIND_ORDER = ["rectorado", "vicerrectorado", "facultad", "escuela", "oficina"]
KIND_LABEL = {
    "rectorado": "Rectorado",
    "vicerrectorado": "Vicerrectorado",
    "facultad": "Facultad",
    "escuela": "Escuela",
    "oficina": "Oficina",
}


def org_levels(params: dict[str, Any], facts: UniversitySnapshot) -> Spec:
    """Cargo -> nivel de la estructura donde esta su unidad (clasificacion)."""
    per_kind = int(params.get("per_kind", 2))
    left: list[dict[str, str]] = []
    pairs: dict[str, str] = {}
    present: list[str] = []
    for kind in KIND_ORDER:
        titles = sorted({p.title for p in facts.positions if p.unit_kind == kind})[:per_kind]
        if titles:
            present.append(kind)
        for title in titles:
            item_id = f"pos-{len(left)}"
            left.append({"id": item_id, "label": title})
            pairs[item_id] = kind
    if not left:
        raise InvalidExerciseSpec("no hay cargos en la BD para generar `org_levels`")
    return {
        "prompt": "Clasifica cada cargo según el nivel de la estructura de la UNSA en el que "
        "se ubica su unidad.",
        "left": left,
        "right": [{"id": k, "label": KIND_LABEL[k]} for k in present],
        "pairs": pairs,
    }


def responsibility_cases(params: dict[str, Any], facts: UniversitySnapshot) -> Spec:
    """Caso cotidiano -> unidad responsable (quiz)."""
    cases: list[dict[str, str]] = params.get("cases", [])
    distractors = int(params.get("distractors", 3))
    by_code = {u.code: u for u in facts.units}
    offices = sorted((u for u in facts.units if u.kind == "oficina"), key=lambda u: u.code)
    questions: list[dict[str, Any]] = []
    for index, case in enumerate(cases):
        correct = by_code.get(case["unit_code"])
        if correct is None:
            continue
        others = [u for u in offices if u.code != correct.code]
        start = index % max(len(others), 1)
        picked = (others[start:] + others[:start])[:distractors]
        picked.insert(index % (len(picked) + 1), correct)
        questions.append(
            {
                "id": f"c{index}",
                "prompt": case["text"],
                "options": [{"id": u.code, "label": u.name} for u in picked],
                "correct": correct.code,
                "explanation": f"La responsabilidad recae en: {correct.name}.",
            }
        )
    if not questions:
        raise InvalidExerciseSpec("no se pudo generar ningun caso de `responsibility_cases`")
    return {"prompt": "¿Qué unidad de la UNSA debe atender cada situación?", "questions": questions}


def system_owners(params: dict[str, Any], facts: UniversitySnapshot) -> Spec:
    """Sistema -> unidad dueña (clasificacion)."""
    limit = int(params.get("limit", 6))
    systems = sorted(facts.systems, key=lambda s: s.name)[:limit]
    if not systems:
        raise InvalidExerciseSpec("no hay sistemas en la BD para generar `system_owners`")
    owner_names = sorted({s.owner_unit_name for s in systems})
    extras = [
        u.name
        for u in sorted(facts.units, key=lambda u: u.code)
        if u.kind == "oficina" and u.name not in owner_names
    ][:2]
    return {
        "prompt": "¿Qué unidad es dueña de cada sistema de información?",
        "left": [{"id": f"s{i}", "label": s.name} for i, s in enumerate(systems)],
        "right": [{"id": name, "label": name} for name in sorted(owner_names + extras)],
        "pairs": {f"s{i}": s.owner_unit_name for i, s in enumerate(systems)},
    }


GENERATORS: dict[str, Callable[[dict[str, Any], UniversitySnapshot], Spec]] = {
    "org_levels": org_levels,
    "responsibility_cases": responsibility_cases,
    "system_owners": system_owners,
}


def generate_spec(name: str, params: dict[str, Any], facts: UniversitySnapshot) -> Spec:
    try:
        generator = GENERATORS[name]
    except KeyError as exc:
        raise InvalidExerciseSpec(f"generador desconocido: {name}") from exc
    return generator(params, facts)
