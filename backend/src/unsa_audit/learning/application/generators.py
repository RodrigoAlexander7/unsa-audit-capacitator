"""Generadores de ejercicios desde los hechos de la UNSA ficticia (puros, deterministas)."""

from collections.abc import Callable
from typing import Any

from unsa_audit.learning.application.ports import PimsFact, UniversitySnapshot
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


FINDING_BY_STATE = {
    "in_force": "conforme",
    "unowned": "observacion",
    "draft": "no_conformidad",
    "expired": "no_conformidad",
    "missing": "no_conformidad",
}
FINDING_LABEL = {
    "conforme": "Conforme",
    "observacion": "Observación",
    "no_conformidad": "No conformidad",
}


def _evidence_text(fact: PimsFact) -> str:
    title = fact.document_title or ""
    if fact.state == "missing":
        return "No existe ningún documento."
    if fact.state == "draft":
        return f"Existe «{title}», pero está en borrador."
    if fact.state == "expired":
        when = fact.review_date.isoformat() if fact.review_date else "?"
        return f"Existe «{title}», vigente, pero su revisión venció el {when}."
    if fact.state == "unowned":
        return f"Existe «{title}», vigente, pero no tiene unidad responsable."
    owner = fact.owner_unit_name or "—"
    return f"Existe «{title}» (v{fact.version}), vigente y con responsable: {owner}."


def pims_audit_findings(params: dict[str, Any], facts: UniversitySnapshot) -> Spec:
    """Evidencia real de cada requisito del PIMS -> tipo de hallazgo (clasificacion)."""
    if not facts.pims:
        raise InvalidExerciseSpec("no hay requisitos PIMS para generar `pims_audit_findings`")
    left = [
        {"id": f.code, "label": f"{f.clause_ref} {f.title}. {_evidence_text(f)}"}
        for f in facts.pims
    ]
    return {
        "prompt": "Auditas el conjunto documental del PIMS de la UNSA. Clasifica el hallazgo "
        "que corresponde a la evidencia de cada requisito.",
        "left": left,
        "right": [{"id": key, "label": label} for key, label in FINDING_LABEL.items()],
        "pairs": {f.code: FINDING_BY_STATE[f.state] for f in facts.pims},
    }


def _audit_question_for(fact: PimsFact) -> str:
    if fact.summary:
        return (
            f"¿La UNSA dispone y mantiene evidencia para «{fact.title}» ({fact.summary.strip()})?"
        )
    return f"¿Existe evidencia vigente y responsable asignado para «{fact.title}»?"


def _audit_evidence_for(fact: PimsFact) -> str:
    if fact.expected_evidence:
        return fact.expected_evidence.strip()
    return f"Documento vigente y aprobado correspondiente a «{fact.title}»."


def audit_checklist_from_pims(params: dict[str, Any], facts: UniversitySnapshot) -> Spec:
    """Lista de verificacion de auditoria generada desde pims_requirements y estado real."""
    if not facts.pims:
        raise InvalidExerciseSpec("no hay requisitos PIMS para generar `audit_checklist_from_pims`")
    limit = int(params.get("limit", len(facts.pims)))
    selected = facts.pims[:limit]
    all_facts = facts.pims
    verdicts = [{"id": key, "label": label} for key, label in FINDING_LABEL.items()]
    items: list[dict[str, Any]] = []

    for idx, fact in enumerate(selected):
        others = [o for o in all_facts if o.code != fact.code]
        if len(others) >= 2:
            d1, d2 = others[idx % len(others)], others[(idx + 1) % len(others)]
            q_distractors = [
                {"id": f"q-dist-{d1.code}", "label": _audit_question_for(d1)},
                {"id": f"q-dist-{d2.code}", "label": _audit_question_for(d2)},
            ]
            e_distractors = [
                {"id": f"e-dist-{d1.code}", "label": _audit_evidence_for(d1)},
                {"id": f"e-dist-{d2.code}", "label": _audit_evidence_for(d2)},
            ]
        else:
            q_distractors = [
                {
                    "id": "q-dist-gen-1",
                    "label": "¿El personal recuerda verbalmente dónde se archiva la documentación?",
                },
                {
                    "id": "q-dist-gen-2",
                    "label": "¿Se contrató un proveedor externo sin revisar requisitos legales?",
                },
            ]
            e_distractors = [
                {
                    "id": "e-dist-gen-1",
                    "label": "Declaración verbal informal sin registro documental.",
                },
                {
                    "id": "e-dist-gen-2",
                    "label": "Lista de asistencia sin evaluación ni documento de respaldo.",
                },
            ]

        q_ok = f"q-ok-{fact.code}"
        e_ok = f"e-ok-{fact.code}"
        verdict = FINDING_BY_STATE[fact.state]
        items.append(
            {
                "id": fact.code,
                "clause_ref": fact.clause_ref,
                "requirement_title": fact.title,
                "observed_context": _evidence_text(fact),
                "questions": [{"id": q_ok, "label": _audit_question_for(fact)}, *q_distractors],
                "evidences": [{"id": e_ok, "label": _audit_evidence_for(fact)}, *e_distractors],
                "expected_question": q_ok,
                "expected_evidence": e_ok,
                "expected_verdict": verdict,
                "explanation": (
                    f"Requisito {fact.clause_ref} ({fact.title}): "
                    f"estado observado '{fact.state}' → {FINDING_LABEL[verdict]}."
                ),
            }
        )

    return {
        "prompt": "Construye la lista de verificación de auditoría interna del PIMS: elige la "
        "pregunta pertinente, la evidencia objetiva a solicitar y el veredicto coherente.",
        "scenario": "Auditoría interna al conjunto documental del PIMS de la UNSA. Evalúa cada "
        "cláusula según el estado real observado en el repositorio institucional.",
        "verdicts": verdicts,
        "items": items,
    }


GENERATORS: dict[str, Callable[[dict[str, Any], UniversitySnapshot], Spec]] = {
    "pims_audit_findings": pims_audit_findings,
    "audit_checklist_from_pims": audit_checklist_from_pims,
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
