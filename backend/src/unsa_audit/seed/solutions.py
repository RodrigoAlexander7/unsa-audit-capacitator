"""Resuelve ejercicios a partir de su spec privada (para el seed demo y para los tests)."""

from datetime import date, timedelta
from typing import Any

from unsa_audit.learning.domain.route import ExerciseKind


def _solve_document_form(spec: dict[str, Any]) -> dict[str, Any]:
    fields_out: dict[str, Any] = {}
    for sec in spec["sections"]:
        for f in sec["fields"]:
            fid, ftype, v = f["id"], f["type"], f["validation"]
            if "sample_solution" in v:
                fields_out[fid] = v["sample_solution"]
            elif "exact" in v:
                fields_out[fid] = v["exact"]
            elif "accepted" in v:
                fields_out[fid] = v["accepted"][0]
            elif "exact_ids" in v:
                fields_out[fid] = list(v["exact_ids"])
            elif "required_ids" in v:
                fields_out[fid] = list(v["required_ids"])
            elif "rubric" in v:
                tokens: list[str] = []
                for crit in v["rubric"]["criteria"]:
                    if "keywords_any" in crit:
                        tokens.append(crit["keywords_any"][0])
                    elif "keyword_groups" in crit:
                        tokens.extend(g[0] for g in crit["keyword_groups"] if g)
                phrase = (
                    "Se cumple considerando " + ", ".join(tokens) + " conforme a la normativa UNSA."
                )
                min_w = int(v["rubric"].get("min_words", 1))
                words = phrase.split()
                while len(words) < min_w:
                    words.extend(["de", "privacidad", "institucional"])
                fields_out[fid] = " ".join(words)
            elif ftype == "date":
                fields_out[fid] = v.get("min_date") or "2026-06-01"
            elif ftype == "multiselect":
                fields_out[fid] = [f["options"][0]["id"]]
            elif ftype in {"select", "position", "reference"}:
                fields_out[fid] = f["options"][0]["id"]
            else:
                fields_out[fid] = "Texto de ejemplo válido"
    # Ajustar date_order simples si no tuvieron sample_solution
    for rule in spec.get("cross_rules", []):
        if rule["kind"] == "date_order":
            fa, fb = rule["fields"][0], rule["fields"][1]
            da = date.fromisoformat(fields_out[fa])
            min_d = int(rule.get("params", {}).get("min_days", 1))
            fields_out[fb] = (da + timedelta(days=max(min_d, 180))).isoformat()
    return {"fields": fields_out}


def solve(kind: ExerciseKind, spec: dict[str, Any]) -> dict[str, Any]:
    """Respuesta perfecta (100 puntos) para el ejercicio."""
    if kind is ExerciseKind.ORDERING:
        return {"order": list(spec["correct_order"])}
    if kind is ExerciseKind.MATCHING:
        return {"assignments": dict(spec["pairs"])}
    if kind is ExerciseKind.SINGLE_CHOICE:
        return {"choice": spec["correct"]}
    if kind is ExerciseKind.QUIZ:
        return {"answers": {q["id"]: q["correct"] for q in spec["questions"]}}
    if kind is ExerciseKind.SOA_FORM:
        return {
            "decisions": {
                c["id"]: {"applies": c["applies"], "reason": c["reason"]} for c in spec["controls"]
            }
        }
    if kind is ExerciseKind.DOCUMENT_FORM:
        return _solve_document_form(spec)
    if kind is ExerciseKind.RISK_TABLE:
        rows = {}
        for r in spec["rows"]:
            entry: dict[str, Any] = {
                "consequence": r["expected_consequence"],
                "probability": r["expected_probability"],
            }
            for opt_k, exp_k in (
                ("threat", "expected_threat"),
                ("vulnerability", "expected_vulnerability"),
                ("risk_owner", "expected_risk_owner"),
            ):
                if exp_k in r:
                    entry[opt_k] = r[exp_k]
            rows[r["id"]] = entry
        return {"rows": rows}
    if kind is ExerciseKind.TREATMENT_TABLE:
        return {
            "rows": {
                r["id"]: {
                    "option": r["expected_option"],
                    "control_id": r.get("expected_control", ""),
                    "owner": r["expected_owner"],
                    "deadline": r["expected_deadline"],
                    "residual_consequence": r["expected_residual_c"],
                    "residual_probability": r["expected_residual_p"],
                }
                for r in spec["rows"]
            }
        }
    if kind is ExerciseKind.AUDIT_CHECKLIST:
        return {
            "items": {
                it["id"]: {
                    "question_id": it["expected_question"],
                    "evidence_id": it["expected_evidence"],
                    "verdict": it["expected_verdict"],
                }
                for it in spec["items"]
            }
        }
    if kind is ExerciseKind.NONCONFORMITY_FORM:
        cases = {}
        for c in spec["cases"]:
            imp = c["max_implementation_date"]
            lag = int(c.get("min_verification_lag_days", 1))
            ver_d = (date.fromisoformat(imp) + timedelta(days=lag)).isoformat()
            cases[c["id"]] = {
                "correction": c["expected_correction"],
                "root_cause": c["expected_root_cause"],
                "requires_action": c["expected_requires_action"],
                "action": c["expected_action"],
                "responsible": c["expected_responsible"],
                "implementation_date": imp,
                "verification_date": ver_d,
                "verification": c["expected_verification"],
                "doc_change": c["expected_doc_change"],
                "affected_document": c.get("expected_document", ""),
            }
        return {"cases": cases}
    if kind is ExerciseKind.COMPETENCE_MATRIX:
        has_eval = "evaluators" in spec
        rows = {}
        for r in spec["rows"]:
            entry_c: dict[str, Any] = {
                "competency_id": r["expected_competency"],
                "training_id": r["expected_training"],
                "evidence_id": r["expected_evidence"],
            }
            if has_eval:
                entry_c["evaluator_id"] = r.get("expected_evaluator") or r["valid_evaluators"][0]
            rows[r["id"]] = entry_c
        return {"rows": rows}
    return {
        "choices": {
            step["id"]: max(step["options"], key=lambda o: o["points"])["id"]
            for step in spec["steps"]
        }
    }


def wrong(kind: ExerciseKind) -> dict[str, Any]:
    """Respuesta vacia de forma valida: puntaje 0 (o minimo)."""
    return {
        ExerciseKind.ORDERING: {"order": []},
        ExerciseKind.MATCHING: {"assignments": {}},
        ExerciseKind.SINGLE_CHOICE: {"choice": "no-existe"},
        ExerciseKind.QUIZ: {"answers": {}},
        ExerciseKind.BRANCHING: {"choices": {}},
        ExerciseKind.SOA_FORM: {"decisions": {}},
        ExerciseKind.DOCUMENT_FORM: {"fields": {}},
        ExerciseKind.RISK_TABLE: {"rows": {}},
        ExerciseKind.TREATMENT_TABLE: {"rows": {}},
        ExerciseKind.AUDIT_CHECKLIST: {"items": {}},
        ExerciseKind.NONCONFORMITY_FORM: {"cases": {}},
        ExerciseKind.COMPETENCE_MATRIX: {"rows": {}},
    }[kind]
