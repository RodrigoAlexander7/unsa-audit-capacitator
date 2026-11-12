"""Validacion, version publica, correccion determinista y guia para practica documental.

Cubre los 6 tipos de ejercicio de la Spec 009 (F8):
- document_form
- risk_table
- treatment_table
- audit_checklist
- nonconformity_form
- competence_matrix

Modulo de dominio puro: sin I/O, sin frameworks, sin dependencias de infraestructura.
"""

import random
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

Spec = dict[str, Any]

_FIELD_TYPES = frozenset(
    {"text", "textarea", "select", "multiselect", "date", "position", "reference"}
)
_CROSS_RULE_KINDS = frozenset(
    {"date_order", "disjoint", "requires_if", "unit_system_coherence", "count_matches"}
)
_VERDICT_IDS = frozenset({"conforme", "observacion", "no_conformidad"})
_TREATMENT_OPTIONS = frozenset({"controls", "transfer", "avoid", "accept"})


class DocSpecError(ValueError):
    """Error de definicion en una spec de practica documental."""


class DocAnswerError(ValueError):
    """Error de forma en la respuesta del participante."""


@dataclass(frozen=True)
class DocItemFeedback:
    id: str
    correct: bool
    feedback: str = ""


@dataclass(frozen=True)
class DocGradeResult:
    score: int
    items: tuple[DocItemFeedback, ...]


@dataclass(frozen=True)
class SolutionGuideItem:
    id: str
    label: str
    expected_summary: str


# ----------------------------------------------------------------------------- utilidades puras


def _need(cond: bool, message: str) -> None:
    if not cond:
        raise DocSpecError(message)


def _list_of_dicts(value: Any, what: str, *, allow_empty: bool = False) -> list[dict[str, Any]]:
    if not isinstance(value, list) or (not allow_empty and not value):
        raise DocSpecError(f"{what} debe ser una lista no vacia")
    if not all(isinstance(x, dict) for x in value):
        raise DocSpecError(f"{what}: cada elemento debe ser un objeto")
    return value


def _req_id(item: dict[str, Any], what: str) -> str:
    raw = item.get("id")
    if not isinstance(raw, str) or not raw:
        raise DocSpecError(f"{what} sin id")
    return raw


def _pct_float(earned: float, total: float) -> int:
    if total <= 0:
        return 0
    return max(0, min(100, round(100.0 * earned / total)))


def _labelled_ids(items: Any, what: str) -> list[str]:
    _need(isinstance(items, list) and len(items) > 0, f"{what} debe ser una lista no vacia")
    ids: list[str] = []
    for item in items:
        ok = isinstance(item, dict) and isinstance(item.get("id"), str) and bool(item.get("label"))
        _need(ok, f"{what}: cada elemento necesita id y label")
        ids.append(item["id"])
    _need(len(set(ids)) == len(ids), f"{what}: ids repetidos")
    return ids


def _strip_opts(options: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [{"id": str(o["id"]), "label": str(o["label"])} for o in options]


def _shuffled_opts(options: list[dict[str, Any]], seed: str) -> list[dict[str, str]]:
    items = _strip_opts(options)
    random.Random(seed).shuffle(items)
    return items


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.lower())
    without_accents = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", without_accents).strip()


def _contains_phrase(norm_text: str, phrase: str) -> bool:
    norm_phrase = _normalize(phrase)
    if not norm_phrase:
        return False
    return bool(re.search(rf"(?<!\w){re.escape(norm_phrase)}(?!\w)", norm_text))


def _parse_iso_date(value: Any) -> date | None:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value.strip()):
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def _expect_dict(container: Any, key: str) -> dict[str, Any]:
    if not isinstance(container, dict) or not isinstance(container.get(key), dict):
        raise DocAnswerError(f"`{key}` debe ser un objeto")
    return container[key]


def _expect_str(row: dict[str, Any], key: str, default: str = "") -> str:
    val = row.get(key, default)
    if not isinstance(val, str):
        raise DocAnswerError(f"`{key}` debe ser texto")
    return val


def _expect_bool(row: dict[str, Any], key: str) -> bool | None:
    if key not in row or row[key] is None:
        return None
    val = row[key]
    if not isinstance(val, bool):
        raise DocAnswerError(f"`{key}` debe ser booleano")
    return val


def _expect_scale(row: dict[str, Any], key: str) -> int | None:
    if key not in row or row[key] is None:
        return None
    val = row[key]
    if isinstance(val, bool) or not isinstance(val, int) or val not in (0, 1, 2):
        raise DocAnswerError(f"`{key}` debe ser entero 0, 1 o 2")
    return val


def _opt_labels(options: list[dict[str, Any]]) -> dict[str, str]:
    return {str(o["id"]): str(o["label"]) for o in options}


# ----------------------------------------------------------------------------- document_form


def _iter_doc_fields(spec: Spec) -> list[dict[str, Any]]:
    return [f for sec in spec.get("sections", []) for f in sec.get("fields", [])]


def _validate_rubric(rubric: Any, fid: str) -> None:
    _need(isinstance(rubric, dict), f"campo {fid}: `rubric` debe ser objeto")
    min_words = rubric.get("min_words", 1)
    _need(isinstance(min_words, int) and min_words >= 1, f"campo {fid}: `min_words` >= 1")
    criteria = rubric.get("criteria")
    _need(isinstance(criteria, list) and len(criteria) > 0, f"campo {fid}: `criteria` vacio")
    for c in criteria:
        has_kw = isinstance(c.get("keywords_any"), list) or isinstance(
            c.get("keyword_groups"), list
        )
        ok = (
            isinstance(c, dict)
            and bool(c.get("id"))
            and bool(c.get("label"))
            and has_kw
            and bool(c.get("feedback_missing"))
        )
        _need(ok, f"campo {fid}: criterio de rubrica incompleto")


def validate_document_form(spec: Spec) -> None:
    _need(bool(spec.get("scenario")), "falta `scenario`")
    _need(bool(spec.get("document_title")), "falta `document_title`")
    sections = _list_of_dicts(spec.get("sections"), "sections")
    sec_ids: list[str] = []
    field_ids: list[str] = []
    for sec in sections:
        sid = _req_id(sec, "seccion")
        _need(bool(sec.get("title")), f"seccion {sid}: falta `title`")
        sec_ids.append(sid)
        fields = _list_of_dicts(sec.get("fields"), f"seccion {sid}.fields")
        for field in fields:
            fid = _req_id(field, "campo")
            _need(bool(field.get("label")), f"campo {fid}: falta `label`")
            ftype = field.get("type")
            _need(ftype in _FIELD_TYPES, f"campo {fid}: tipo invalido `{ftype}`")
            if ftype in {"select", "multiselect", "position", "reference"}:
                _labelled_ids(field.get("options"), f"campo {fid}.options")
            validation = field.get("validation")
            if not isinstance(validation, dict):
                raise DocSpecError(f"campo {fid}: falta `validation`")
            if "rubric" in validation:
                _validate_rubric(validation["rubric"], fid)
            field_ids.append(fid)
    _need(len(set(sec_ids)) == len(sec_ids), "ids de seccion repetidos")
    _need(len(set(field_ids)) == len(field_ids), "ids de campo repetidos")

    rules = _list_of_dicts(spec.get("cross_rules", []), "cross_rules", allow_empty=True)
    rule_ids: list[str] = []
    for rule in rules:
        rid = _req_id(rule, "regla")
        _need(rid not in field_ids, f"regla {rid}: id colisiona con un campo")
        _need(rule.get("kind") in _CROSS_RULE_KINDS, f"regla {rid}: tipo invalido")
        rfields = rule.get("fields")
        _need(
            isinstance(rfields, list)
            and len(rfields) >= 2
            and all(f in field_ids for f in rfields),
            f"regla {rid}: `fields` debe referenciar >= 2 campos existentes",
        )
        _need(bool(rule.get("feedback")), f"regla {rid}: falta `feedback`")
        rule_ids.append(rid)
    _need(len(set(rule_ids)) == len(rule_ids), "ids de regla repetidos")


def public_document_form(spec: Spec) -> Spec:
    sections_pub = []
    for sec in spec["sections"]:
        fields_pub = []
        for f in sec["fields"]:
            item: dict[str, Any] = {
                "id": f["id"],
                "label": f["label"],
                "type": f["type"],
                "required": bool(f.get("required", True)),
            }
            for opt_key in ("help", "placeholder"):
                if f.get(opt_key):
                    item[opt_key] = f[opt_key]
            if "options" in f:
                item["options"] = _strip_opts(f["options"])
            fields_pub.append(item)
        sec_item: dict[str, Any] = {"id": sec["id"], "title": sec["title"], "fields": fields_pub}
        if sec.get("description"):
            sec_item["description"] = sec["description"]
        sections_pub.append(sec_item)
    return {
        "prompt": spec["prompt"],
        "scenario": spec["scenario"],
        "document_title": spec["document_title"],
        "sections": sections_pub,
    }


def _grade_rubric_text(raw: str, rubric: dict[str, Any]) -> tuple[float, bool, str]:
    norm = _normalize(raw)
    for anti in rubric.get("forbidden_any", []):
        if any(_contains_phrase(norm, p) for p in anti.get("phrases", [])):
            return 0.0, False, anti.get("feedback", "Incluye un planteamiento inválido.")
    words = [w for w in norm.split(" ") if w]
    min_words = rubric.get("min_words", 1)
    if len(words) < min_words:
        return (
            0.0,
            False,
            f"Redacción demasiado breve ({len(words)} palabras; mínimo {min_words} útiles).",
        )

    criteria = rubric["criteria"]
    met = 0
    missing_msgs: list[str] = []
    for crit in criteria:
        ok = False
        if "keywords_any" in crit:
            ok = any(_contains_phrase(norm, kw) for kw in crit["keywords_any"])
        elif "keyword_groups" in crit:
            ok = all(
                any(_contains_phrase(norm, kw) for kw in group) for group in crit["keyword_groups"]
            )
        if ok:
            met += 1
        else:
            missing_msgs.append(crit["feedback_missing"])
    if met == len(criteria):
        return 1.0, True, "Contiene todos los elementos requeridos."
    return met / len(criteria), False, " ".join(missing_msgs)


def _grade_single_field(field: dict[str, Any], raw: Any) -> tuple[float, bool, str]:
    fid = field["id"]
    ftype = field["type"]
    v = field["validation"]
    required = bool(field.get("required", True))
    err_fb = v.get("feedback_error", "El valor ingresado no cumple el criterio esperado.")

    if ftype == "multiselect":
        if raw is None:
            raw = []
        if not isinstance(raw, list) or not all(isinstance(x, str) for x in raw):
            raise DocAnswerError(f"`fields.{fid}` debe ser una lista de identificadores")
        if required and not raw:
            return 0.0, False, "Campo obligatorio sin selección."
        valid_ids = {o["id"] for o in field["options"]}
        if any(x not in valid_ids for x in raw):
            return 0.0, False, "Contiene opciones fuera del catálogo permitido."
        selected = set(raw)
        if "exact_ids" in v:
            expected = set(v["exact_ids"])
            if selected == expected:
                return 1.0, True, "Selección correcta."
            return 0.0, False, err_fb
        req_ids = set(v.get("required_ids", []))
        forb_ids = set(v.get("forbidden_ids", []))
        min_sel = v.get("min_selected", 0)
        missing = req_ids - selected
        forbidden_picked = selected & forb_ids
        if not missing and not forbidden_picked and len(selected) >= min_sel:
            return 1.0, True, "Selección correcta."
        parts: list[str] = []
        if missing:
            parts.append("Falta incluir elementos obligatorios según el escenario.")
        if forbidden_picked:
            parts.append("Incluye elementos excluidos o fuera del alcance del escenario.")
        if len(selected) < min_sel:
            parts.append(f"Selecciona al menos {min_sel} elementos.")
        return 0.0, False, v.get("feedback_error") or " ".join(parts)

    if raw is None:
        raw = ""
    if not isinstance(raw, str):
        raise DocAnswerError(f"`fields.{fid}` debe ser texto")
    text = raw.strip()
    if required and not text:
        return 0.0, False, "Campo obligatorio sin completar."
    if not required and not text:
        return 1.0, True, "Opcional omitido."

    if "rubric" in v:
        return _grade_rubric_text(text, v["rubric"])

    if ftype == "date":
        parsed = _parse_iso_date(text)
        if parsed is None:
            return 0.0, False, "Formato de fecha inválido (usa AAAA-MM-DD)."
        min_d = _parse_iso_date(v.get("min_date"))
        max_d = _parse_iso_date(v.get("max_date"))
        if min_d and parsed < min_d:
            return 0.0, False, err_fb
        if max_d and parsed > max_d:
            return 0.0, False, err_fb

    if ftype in {"select", "position", "reference"}:
        valid_ids = {o["id"] for o in field["options"]}
        if text not in valid_ids:
            return 0.0, False, "Selecciona una opción válida del catálogo."

    if "pattern" in v and not re.fullmatch(v["pattern"], text):
        return 0.0, False, err_fb
    if "exact" in v and text != v["exact"]:
        return 0.0, False, err_fb
    if "accepted" in v and text not in v["accepted"]:
        return 0.0, False, err_fb
    return 1.0, True, "Correcto."


def _eval_cross_rule(rule: dict[str, Any], values: dict[str, Any]) -> tuple[bool, str]:
    kind = rule["kind"]
    a_id, b_id = rule["fields"][0], rule["fields"][1]
    a, b = values.get(a_id), values.get(b_id)
    params = rule.get("params", {})
    fb = rule["feedback"]

    if kind == "date_order":
        da, db = _parse_iso_date(a), _parse_iso_date(b)
        if da is None or db is None:
            return False, fb
        allow_eq = bool(params.get("allow_equal", False))
        if (db < da) or (not allow_eq and db <= da):
            return False, fb
        min_days = params.get("min_days")
        max_days = params.get("max_days")
        diff = (db - da).days
        if min_days is not None and diff < int(min_days):
            return False, fb
        if max_days is not None and diff > int(max_days):
            return False, fb
        return True, "Coherencia temporal correcta."

    if kind == "disjoint":
        if isinstance(a, list) and isinstance(b, list):
            return not (set(a) & set(b)), "Sin conflicto entre campos." if not (
                set(a) & set(b)
            ) else fb
        sa = str(a or "").strip()
        sb = str(b or "").strip()
        ok = bool(sa and sb and sa != sb)
        return ok, "Segregación correcta." if ok else fb

    if kind == "requires_if":
        when_in = set(params.get("when_in", []))
        a_set = set(a) if isinstance(a, list) else ({str(a)} if a else set())
        if not (a_set & when_in):
            return True, "Condición no activada."
        b_set = set(b) if isinstance(b, list) else ({str(b)} if b else set())
        req_all = set(params.get("require_all", []))
        req_any = set(params.get("require_any", []))
        forb = set(params.get("forbid_any", []))
        ok = req_all <= b_set and (not req_any or bool(b_set & req_any)) and not (b_set & forb)
        return ok, "Coherencia entre campos correcta." if ok else fb

    if kind == "unit_system_coherence":
        units = set(a) if isinstance(a, list) else set()
        systems = set(b) if isinstance(b, list) else set()
        if not units or not systems:
            return False, fb
        sys_to_unit: dict[str, str] = params.get("system_to_unit", {})
        support_units = set(params.get("support_units", []))
        for sys_id in systems:
            owner_unit = sys_to_unit.get(sys_id)
            if owner_unit is None or (owner_unit not in units and owner_unit not in support_units):
                return False, fb
        req_by_unit: dict[str, list[str]] = params.get("required_unit_systems", {})
        for unit_id, req_systems in req_by_unit.items():
            if unit_id in units and not (set(req_systems) <= systems):
                return False, fb
        return True, "Coherencia unidades ↔ sistemas verificada."

    # count_matches
    try:
        expected_n = int(str(a).strip())
    except ValueError:
        return False, fb
    if isinstance(b, list):
        actual_n = len(b)
    elif isinstance(b, str):
        actual_n = len([ln for ln in b.splitlines() if ln.strip()])
    else:
        return False, fb
    return (expected_n == actual_n), ("Conteo consistente." if expected_n == actual_n else fb)


def grade_document_form(spec: Spec, answer: Any) -> DocGradeResult:
    fields_ans = _expect_dict(answer, "fields")
    items: list[DocItemFeedback] = []
    earned = 0.0
    total = 0.0

    for field in _iter_doc_fields(spec):
        fid = field["id"]
        pts, ok, fb = _grade_single_field(field, fields_ans.get(fid))
        earned += pts
        total += 1.0
        items.append(DocItemFeedback(fid, ok, fb))

    for rule in spec.get("cross_rules", []):
        ok, fb = _eval_cross_rule(rule, fields_ans)
        earned += 1.0 if ok else 0.0
        total += 1.0
        items.append(DocItemFeedback(rule["id"], ok, fb))

    return DocGradeResult(_pct_float(earned, total), tuple(items))


def guide_document_form(spec: Spec, failed_ids: set[str]) -> list[SolutionGuideItem]:
    guides: list[SolutionGuideItem] = []
    for field in _iter_doc_fields(spec):
        fid = field["id"]
        if fid not in failed_ids:
            continue
        v = field["validation"]
        if v.get("expected_summary"):
            summary = v["expected_summary"]
        elif "exact" in v:
            labels = _opt_labels(field["options"]) if "options" in field else {}
            summary = f"Valor esperado: {labels.get(v['exact'], v['exact'])}."
        elif "accepted" in v:
            labels = _opt_labels(field["options"]) if "options" in field else {}
            opts = ", ".join(labels.get(str(x), str(x)) for x in v["accepted"])
            summary = f"Opciones válidas: {opts}."
        elif "exact_ids" in v or "required_ids" in v:
            labels = _opt_labels(field["options"])
            req = v.get("exact_ids") or v.get("required_ids", [])
            summary = "Debe incluir: " + ", ".join(labels.get(str(x), str(x)) for x in req) + "."
        elif "rubric" in v:
            crit_lbls = "; ".join(c["label"] for c in v["rubric"]["criteria"])
            summary = f"Debe abordar: {crit_lbls}."
        else:
            summary = v.get("feedback_error", "Revisa el formato y criterio del campo.")
        guides.append(SolutionGuideItem(fid, field["label"], summary))

    for rule in spec.get("cross_rules", []):
        if rule["id"] in failed_ids:
            guides.append(
                SolutionGuideItem(
                    rule["id"],
                    rule.get("label") or f"Coherencia ({', '.join(rule['fields'])})",
                    rule.get("expected_summary") or rule["feedback"],
                )
            )
    return guides


# ----------------------------------------------------------------------------- risk_table


def validate_risk_table(spec: Spec) -> None:
    _need(bool(spec.get("scenario")), "falta `scenario`")
    rows = _list_of_dicts(spec.get("rows"), "rows")
    ids: list[str] = []
    for row in rows:
        rid = _req_id(row, "fila")
        _need(bool(row.get("asset")) and bool(row.get("asset_owner")), f"fila {rid}: falta activo")
        _need(isinstance(row.get("sensitive_data"), bool), f"fila {rid}: `sensitive_data` bool")
        ec, ep = row.get("expected_consequence"), row.get("expected_probability")
        _need(ec in (0, 1, 2) and ep in (0, 1, 2), f"fila {rid}: C/P esperados deben ser 0..2")
        if row["sensitive_data"]:
            _need(ec == 2, f"fila {rid}: datos sensibles exigen expected_consequence = 2")
        _need(bool(row.get("explanation")), f"fila {rid}: falta `explanation`")
        for opt_key, exp_key in (
            ("threat_options", "expected_threat"),
            ("vulnerability_options", "expected_vulnerability"),
            ("risk_owner_options", "expected_risk_owner"),
        ):
            if opt_key in row:
                opts = _labelled_ids(row[opt_key], f"fila {rid}.{opt_key}")
                _need(row.get(exp_key) in opts, f"fila {rid}: falta `{exp_key}` valido")
        ids.append(rid)
    _need(len(set(ids)) == len(ids), "ids de fila repetidos")


def public_risk_table(spec: Spec, seed: str) -> Spec:
    rows_pub = []
    for r in spec["rows"]:
        item: dict[str, Any] = {
            "id": r["id"],
            "asset": r["asset"],
            "asset_owner": r["asset_owner"],
            "data_categories": list(r.get("data_categories", [])),
            "existing_controls": r.get("existing_controls", ""),
            "threat": r.get("threat", ""),
            "vulnerability": r.get("vulnerability", ""),
            "risk_owner": r.get("risk_owner", ""),
        }
        for opt_key in ("threat_options", "vulnerability_options", "risk_owner_options"):
            if opt_key in r:
                item[opt_key] = _shuffled_opts(r[opt_key], f"{seed}:{r['id']}:{opt_key}")
        rows_pub.append(item)
    return {
        "prompt": spec["prompt"],
        "scenario": spec["scenario"],
        "threshold": int(spec.get("threshold", 3)),
        "rows": rows_pub,
    }


def grade_risk_table(spec: Spec, answer: Any) -> DocGradeResult:
    rows_ans = _expect_dict(answer, "rows")
    threshold = int(spec.get("threshold", 3))
    items: list[DocItemFeedback] = []
    earned = 0.0

    for row in spec["rows"]:
        rid = row["id"]
        raw = rows_ans.get(rid)
        if raw is not None and not isinstance(raw, dict):
            raise DocAnswerError(f"`rows.{rid}` debe ser un objeto")
        raw = raw or {}
        c = _expect_scale(raw, "consequence")
        p = _expect_scale(raw, "probability")

        # Validacion de forma de selects opcionales antes de responder
        threat = _expect_str(raw, "threat") if "threat" in raw else ""
        vuln = _expect_str(raw, "vulnerability") if "vulnerability" in raw else ""
        owner = _expect_str(raw, "risk_owner") if "risk_owner" in raw else ""

        if c is None or p is None:
            items.append(DocItemFeedback(rid, False, "Falta valorar consecuencia y probabilidad."))
            continue

        reasons: list[str] = []
        sub_checks: list[bool] = []

        for opt_key, exp_key, val, label in (
            ("threat_options", "expected_threat", threat, "amenaza"),
            ("vulnerability_options", "expected_vulnerability", vuln, "vulnerabilidad"),
            ("risk_owner_options", "expected_risk_owner", owner, "propietario del riesgo"),
        ):
            if opt_key in row:
                ok_field = val == row[exp_key]
                sub_checks.append(ok_field)
                if not ok_field:
                    reasons.append(f"Revisa la selección de {label}.")

        calc_risk = c + p
        ec, ep = row["expected_consequence"], row["expected_probability"]
        exp_risk = ec + ep
        tol = int(row.get("tolerance", 0))

        sensitive_ok = not (row["sensitive_data"] and c < 2)
        if not sensitive_ok:
            reasons.append(
                "Este activo trata datos sensibles: la metodología UNSA exige consecuencia 2 "
                "(alta)."
            )
        threshold_ok = (calc_risk >= threshold) == (exp_risk >= threshold)
        if not threshold_ok:
            reasons.append(
                f"El nivel calculado ({calc_risk}) cruza el umbral de aceptación "
                f"(>= {threshold} es no aceptable)."
            )

        if tol == 0:
            score_ok = c == ec and p == ep
            if not score_ok and sensitive_ok and threshold_ok:
                if c != ec:
                    reasons.append(
                        "Consecuencia desviada respecto al impacto real sobre titulares."
                    )
                if p != ep:
                    reasons.append("Probabilidad incoherente con los controles existentes.")
        else:
            score_ok = abs(calc_risk - exp_risk) <= tol
            if not score_ok and sensitive_ok and threshold_ok:
                reasons.append(f"Riesgo calculado ({calc_risk}) fuera del rango esperado.")

        rating_ok = sensitive_ok and threshold_ok and score_ok
        sub_checks.append(rating_ok)
        row_ok = all(sub_checks)
        earned += sum(sub_checks) / len(sub_checks)
        fb = "Valoración correcta." if row_ok else " ".join([*reasons, row["explanation"]])
        items.append(DocItemFeedback(rid, row_ok, fb))

    return DocGradeResult(_pct_float(earned, len(spec["rows"])), tuple(items))


def guide_risk_table(spec: Spec, failed_ids: set[str]) -> list[SolutionGuideItem]:
    guides: list[SolutionGuideItem] = []
    for r in spec["rows"]:
        if r["id"] not in failed_ids:
            continue
        ec, ep = r["expected_consequence"], r["expected_probability"]
        guides.append(
            SolutionGuideItem(
                r["id"],
                r["asset"],
                f"Valoración esperada: C={ec}, P={ep} (riesgo={ec + ep}). {r['explanation']}",
            )
        )
    return guides


# ----------------------------------------------------------------------------- treatment_table


def validate_treatment_table(spec: Spec) -> None:
    _need(bool(spec.get("scenario")), "falta `scenario`")
    opt_ids = _labelled_ids(spec.get("options"), "options")
    _need(set(opt_ids) <= _TREATMENT_OPTIONS, "opciones de tratamiento invalidas")
    soa = _list_of_dicts(spec.get("soa_controls"), "soa_controls")
    soa_ids = _labelled_ids(soa, "soa_controls")
    for c in soa:
        _need(isinstance(c.get("soa_applies"), bool), f"control {c['id']}: falta `soa_applies`")
    owner_ids = _labelled_ids(spec.get("owners"), "owners")

    rows = _list_of_dicts(spec.get("rows"), "rows")
    row_ids: list[str] = []
    for r in rows:
        rid = _req_id(r, "fila")
        _need(r.get("expected_option") in opt_ids, f"fila {rid}: `expected_option` invalido")
        _need(
            r.get("expected_option") in r.get("valid_options", []),
            f"fila {rid}: `expected_option` debe estar en `valid_options`",
        )
        if r["expected_option"] == "controls":
            _need(
                r.get("expected_control") in soa_ids,
                f"fila {rid}: `expected_control` inexistente",
            )
        _need(r.get("expected_owner") in owner_ids, f"fila {rid}: `expected_owner` inexistente")
        _need(
            _parse_iso_date(r.get("expected_deadline")) is not None,
            f"fila {rid}: `expected_deadline` invalida",
        )
        _need(
            r.get("expected_residual_c") in (0, 1, 2) and r.get("expected_residual_p") in (0, 1, 2),
            f"fila {rid}: residual esperado 0..2",
        )
        _need(bool(r.get("explanation")), f"fila {rid}: falta `explanation`")
        row_ids.append(rid)
    _need(len(set(row_ids)) == len(row_ids), "ids de fila repetidos")


def public_treatment_table(spec: Spec) -> Spec:
    return {
        "prompt": spec["prompt"],
        "scenario": spec["scenario"],
        "options": _strip_opts(spec["options"]),
        "soa_controls": _strip_opts(spec["soa_controls"]),
        "owners": _strip_opts(spec["owners"]),
        "rows": [
            {
                "id": r["id"],
                "asset": r["asset"],
                "threat": r["threat"],
                "vulnerability": r["vulnerability"],
                "initial_consequence": r["initial_consequence"],
                "initial_probability": r["initial_probability"],
                "initial_risk": r["initial_risk"],
                "risk_owner": r["risk_owner"],
            }
            for r in spec["rows"]
        ],
    }


def grade_treatment_table(spec: Spec, answer: Any) -> DocGradeResult:
    rows_ans = _expect_dict(answer, "rows")
    soa_map = {c["id"]: c for c in spec["soa_controls"]}
    items: list[DocItemFeedback] = []
    earned = 0.0

    for row in spec["rows"]:
        rid = row["id"]
        raw = rows_ans.get(rid)
        if raw is not None and not isinstance(raw, dict):
            raise DocAnswerError(f"`rows.{rid}` debe ser un objeto")
        raw = raw or {}
        opt = _expect_str(raw, "option")
        ctrl = _expect_str(raw, "control_id")
        owner = _expect_str(raw, "owner")
        deadline_str = _expect_str(raw, "deadline")
        rc = _expect_scale(raw, "residual_consequence")
        rp = _expect_scale(raw, "residual_probability")

        if not opt or rc is None or rp is None:
            items.append(DocItemFeedback(rid, False, "Completa opción y valoración residual."))
            continue

        reasons: list[str] = []
        # 1) Opcion
        opt_ok = opt in row.get("valid_options", [])
        if opt == "accept" and not row.get("allow_accept", False):
            opt_ok = False
            reasons.append("No es aceptable asumir este riesgo sin tratamiento dado su impacto.")
        elif not opt_ok:
            reasons.append("La opción elegida no es adecuada para este riesgo.")

        # 2) Control SoA coherente con opcion
        if opt == "controls":
            c_obj = soa_map.get(ctrl)
            if c_obj is None:
                ctrl_ok = False
                reasons.append("Debes seleccionar un control de la Declaración de Aplicabilidad.")
            elif not c_obj["soa_applies"]:
                ctrl_ok = False
                reasons.append("Ese control figura como «No aplica» en la SoA.")
            elif ctrl not in row.get("valid_controls", []):
                ctrl_ok = False
                reasons.append("El control elegido no mitiga esta amenaza/vulnerabilidad.")
            else:
                ctrl_ok = True
        elif opt == "accept":
            ctrl_ok = ctrl in ("", "none")
            if not ctrl_ok:
                reasons.append("Si aceptas el riesgo no debes asociar controles nuevos.")
        elif opt == "avoid":
            ctrl_ok = ctrl in ("", "none")
            if not ctrl_ok:
                reasons.append("Al evitar la actividad no se requiere control adicional.")
        else:  # transfer
            valid_tr = row.get("valid_controls", [])
            ctrl_ok = (not valid_tr and ctrl in ("", "none")) or (ctrl in valid_tr)
            if not ctrl_ok:
                reasons.append("La transferencia exige un control contractual/acuerdo pertinente.")

        # 3) Responsable
        owner_ok = owner in row.get("valid_owners", [])
        if not owner_ok:
            reasons.append("El responsable asignado no corresponde a la unidad dueña o competente.")

        # 4) Plazo
        d_val = _parse_iso_date(deadline_str)
        min_d = _parse_iso_date(row.get("min_deadline"))
        max_d = _parse_iso_date(row.get("max_deadline"))
        deadline_ok = (
            d_val is not None and (not min_d or d_val >= min_d) and (not max_d or d_val <= max_d)
        )
        if not deadline_ok:
            reasons.append("El plazo es inválido o cae fuera del horizonte del plan.")

        # 5) Riesgo residual
        res_risk = rc + rp
        exp_res = row["expected_residual_c"] + row["expected_residual_p"]
        tol = int(row.get("residual_tolerance", 0))
        init_risk = int(row["initial_risk"])
        if (
            rc > row["initial_consequence"]
            or rp > row["initial_probability"]
            or res_risk > init_risk
        ):
            res_ok = False
            reasons.append("El tratamiento no puede incrementar el riesgo residual.")
        elif opt == "accept" and res_risk != init_risk:
            res_ok = False
            reasons.append("Aceptar un riesgo mantiene el nivel residual igual al inicial.")
        elif opt == "avoid" and res_risk != 0:
            res_ok = False
            reasons.append("Evitar la actividad elimina el riesgo residual (0).")
        elif tol == 0:
            res_ok = rc == row["expected_residual_c"] and rp == row["expected_residual_p"]
            if not res_ok:
                reasons.append(
                    f"Riesgo residual esperado distinto del calculado ({res_risk} vs {exp_res})."
                )
        else:
            res_ok = abs(res_risk - exp_res) <= tol
            if not res_ok:
                reasons.append("Riesgo residual fuera del rango esperado.")

        checks = [opt_ok, ctrl_ok, owner_ok, deadline_ok, res_ok]
        row_ok = all(checks)
        earned += sum(checks) / len(checks)
        fb = "Tratamiento coherente." if row_ok else " ".join([*reasons, row["explanation"]])
        items.append(DocItemFeedback(rid, row_ok, fb))

    return DocGradeResult(_pct_float(earned, len(spec["rows"])), tuple(items))


def guide_treatment_table(spec: Spec, failed_ids: set[str]) -> list[SolutionGuideItem]:
    owners = _opt_labels(spec["owners"])
    ctrls = _opt_labels(spec["soa_controls"])
    opts = _opt_labels(spec["options"])
    guides: list[SolutionGuideItem] = []
    for r in spec["rows"]:
        if r["id"] not in failed_ids:
            continue
        ec, ep = r["expected_residual_c"], r["expected_residual_p"]
        ctrl_lbl = ctrls.get(r.get("expected_control", ""), "Ninguno")
        owner_lbl = owners.get(r["expected_owner"], r["expected_owner"])
        guides.append(
            SolutionGuideItem(
                r["id"],
                r["asset"],
                f"Opción: {opts.get(r['expected_option'], r['expected_option'])} · "
                f"Control: {ctrl_lbl} · Responsable: {owner_lbl} · "
                f"Plazo: {r['expected_deadline']} · Residual: C={ec}, P={ep} ({ec + ep}).",
            )
        )
    return guides


# ----------------------------------------------------------------------------- audit_checklist


def validate_audit_checklist(spec: Spec) -> None:
    _need(bool(spec.get("scenario")), "falta `scenario`")
    v_ids = _labelled_ids(spec.get("verdicts"), "verdicts")
    _need(set(v_ids) <= _VERDICT_IDS, "verdictos invalidos")
    items = _list_of_dicts(spec.get("items"), "items")
    ids: list[str] = []
    for item in items:
        iid = _req_id(item, "item")
        _need(
            bool(item.get("clause_ref"))
            and bool(item.get("requirement_title"))
            and bool(item.get("observed_context")),
            f"item {iid}: faltan metadatos de requisito/contexto",
        )
        q_ids = _labelled_ids(item.get("questions"), f"item {iid}.questions")
        e_ids = _labelled_ids(item.get("evidences"), f"item {iid}.evidences")
        _need(item.get("expected_question") in q_ids, f"item {iid}: `expected_question` invalido")
        _need(item.get("expected_evidence") in e_ids, f"item {iid}: `expected_evidence` invalido")
        _need(item.get("expected_verdict") in v_ids, f"item {iid}: `expected_verdict` invalido")
        _need(bool(item.get("explanation")), f"item {iid}: falta `explanation`")
        ids.append(iid)
    _need(len(set(ids)) == len(ids), "ids de item repetidos")


def public_audit_checklist(spec: Spec, seed: str) -> Spec:
    return {
        "prompt": spec["prompt"],
        "scenario": spec["scenario"],
        "verdicts": _strip_opts(spec["verdicts"]),
        "items": [
            {
                "id": it["id"],
                "clause_ref": it["clause_ref"],
                "requirement_title": it["requirement_title"],
                "observed_context": it["observed_context"],
                "questions": _shuffled_opts(it["questions"], f"{seed}:{it['id']}:q"),
                "evidences": _shuffled_opts(it["evidences"], f"{seed}:{it['id']}:e"),
            }
            for it in spec["items"]
        ],
    }


def grade_audit_checklist(spec: Spec, answer: Any) -> DocGradeResult:
    ans_items = _expect_dict(answer, "items")
    feedback_list: list[DocItemFeedback] = []
    earned = 0.0

    for item in spec["items"]:
        iid = item["id"]
        raw = ans_items.get(iid)
        if raw is not None and not isinstance(raw, dict):
            raise DocAnswerError(f"`items.{iid}` debe ser un objeto")
        raw = raw or {}
        q = _expect_str(raw, "question_id")
        ev = _expect_str(raw, "evidence_id")
        vd = _expect_str(raw, "verdict")

        q_ok = q == item["expected_question"]
        ev_ok = ev == item["expected_evidence"]
        vd_ok = vd == item["expected_verdict"]

        reasons: list[str] = []
        if not q_ok:
            reasons.append("La pregunta elegida no verifica la cláusula requerida.")
        if not ev_ok:
            reasons.append("La evidencia solicitada no demuestra cumplimiento de este requisito.")
        if not vd_ok:
            reasons.append("El veredicto no corresponde al estado real del documento observado.")

        ok = q_ok and ev_ok and vd_ok
        earned += (int(q_ok) + int(ev_ok) + int(vd_ok)) / 3.0
        fb = "Ítem de auditoría correcto." if ok else " ".join([*reasons, item["explanation"]])
        feedback_list.append(DocItemFeedback(iid, ok, fb))

    return DocGradeResult(_pct_float(earned, len(spec["items"])), tuple(feedback_list))


def guide_audit_checklist(spec: Spec, failed_ids: set[str]) -> list[SolutionGuideItem]:
    verdicts = _opt_labels(spec["verdicts"])
    guides: list[SolutionGuideItem] = []
    for it in spec["items"]:
        if it["id"] not in failed_ids:
            continue
        q_lbl = _opt_labels(it["questions"]).get(it["expected_question"], "")
        e_lbl = _opt_labels(it["evidences"]).get(it["expected_evidence"], "")
        v_lbl = verdicts.get(it["expected_verdict"], it["expected_verdict"])
        guides.append(
            SolutionGuideItem(
                it["id"],
                f"{it['clause_ref']} {it['requirement_title']}",
                f"Pregunta: {q_lbl} · Evidencia: {e_lbl} · Veredicto: {v_lbl}.",
            )
        )
    return guides


# ----------------------------------------------------------------------------- nonconformity_form


def validate_nonconformity_form(spec: Spec) -> None:
    _need(bool(spec.get("scenario")), "falta `scenario`")
    doc_ids = _labelled_ids(spec.get("documents"), "documents")
    pos_ids = _labelled_ids(spec.get("positions"), "positions")
    cases = _list_of_dicts(spec.get("cases"), "cases")
    cids: list[str] = []
    for c in cases:
        cid = _req_id(c, "caso")
        _need(
            bool(c.get("title")) and bool(c.get("detection_context")),
            f"caso {cid}: falta contexto",
        )
        _need(_parse_iso_date(c.get("detection_date")) is not None, f"caso {cid}: fecha deteccion")
        _need(
            _parse_iso_date(c.get("max_implementation_date")) is not None,
            f"caso {cid}: max fecha",
        )
        corr_ids = _labelled_ids(c.get("correction_options"), f"caso {cid}.correction_options")
        root_ids = _labelled_ids(c.get("root_cause_options"), f"caso {cid}.root_cause_options")
        act_ids = _labelled_ids(c.get("action_options"), f"caso {cid}.action_options")
        ver_ids = _labelled_ids(c.get("verification_options"), f"caso {cid}.verification_options")
        _need(
            c.get("expected_correction") in corr_ids,
            f"caso {cid}: `expected_correction` invalido",
        )
        _need(
            c.get("expected_root_cause") in root_ids,
            f"caso {cid}: `expected_root_cause` invalido",
        )
        _need(isinstance(c.get("expected_requires_action"), bool), f"caso {cid}: bool requerido")
        _need(c.get("expected_action") in act_ids, f"caso {cid}: `expected_action` invalido")
        _need(c.get("expected_responsible") in pos_ids, f"caso {cid}: responsable invalido")
        _need(c.get("expected_verification") in ver_ids, f"caso {cid}: verificacion invalida")
        lag = c.get("min_verification_lag_days", 1)
        _need(isinstance(lag, int) and lag >= 1, f"caso {cid}: `min_verification_lag_days` >= 1")
        _need(isinstance(c.get("expected_doc_change"), bool), f"caso {cid}: doc_change bool")
        if c["expected_doc_change"]:
            _need(
                c.get("expected_document") in doc_ids,
                f"caso {cid}: `expected_document` invalido",
            )
        _need(bool(c.get("explanation")), f"caso {cid}: falta `explanation`")
        cids.append(cid)
    _need(len(set(cids)) == len(cids), "ids de caso repetidos")


def public_nonconformity_form(spec: Spec, seed: str) -> Spec:
    return {
        "prompt": spec["prompt"],
        "scenario": spec["scenario"],
        "documents": _strip_opts(spec["documents"]),
        "positions": _strip_opts(spec["positions"]),
        "cases": [
            {
                "id": c["id"],
                "title": c["title"],
                "detection_context": c["detection_context"],
                "detection_date": c["detection_date"],
                "correction_options": _shuffled_opts(
                    c["correction_options"], f"{seed}:{c['id']}:corr"
                ),
                "root_cause_options": _shuffled_opts(
                    c["root_cause_options"], f"{seed}:{c['id']}:root"
                ),
                "action_options": _shuffled_opts(c["action_options"], f"{seed}:{c['id']}:act"),
                "verification_options": _shuffled_opts(
                    c["verification_options"], f"{seed}:{c['id']}:ver"
                ),
            }
            for c in spec["cases"]
        ],
    }


def grade_nonconformity_form(spec: Spec, answer: Any) -> DocGradeResult:
    ans_cases = _expect_dict(answer, "cases")
    feedback_list: list[DocItemFeedback] = []
    earned = 0.0

    for case in spec["cases"]:
        cid = case["id"]
        raw = ans_cases.get(cid)
        if raw is not None and not isinstance(raw, dict):
            raise DocAnswerError(f"`cases.{cid}` debe ser un objeto")
        raw = raw or {}

        corr = _expect_str(raw, "correction")
        root = _expect_str(raw, "root_cause")
        req_act = _expect_bool(raw, "requires_action")
        action = _expect_str(raw, "action")
        resp = _expect_str(raw, "responsible")
        imp_str = _expect_str(raw, "implementation_date")
        ver_str = _expect_str(raw, "verification_date")
        verif = _expect_str(raw, "verification")
        doc_chg = _expect_bool(raw, "doc_change")
        aff_doc = _expect_str(raw, "affected_document")

        if req_act is None or doc_chg is None or not corr or not root or not action:
            feedback_list.append(
                DocItemFeedback(
                    cid, False, "Completa todos los campos de la ficha de no conformidad."
                )
            )
            continue

        reasons: list[str] = []
        corr_ok = corr == case["expected_correction"]
        if not corr_ok:
            reasons.append(
                "La corrección debe contener de inmediato el efecto puntual, no cambiar el proceso."
            )

        root_ok = root == case["expected_root_cause"]
        if not root_ok:
            reasons.append(
                "La causa raíz identifica la falla sistémica o de control, no repite el síntoma."
            )

        act_ok = (req_act is case["expected_requires_action"]) and (
            action == case["expected_action"]
        )
        if not act_ok:
            reasons.append(
                "La acción correctiva elimina la causa raíz para evitar recurrencia "
                "(distinta de la corrección)."
            )

        resp_ok = resp == case["expected_responsible"]
        if not resp_ok:
            reasons.append("Responsable asignado no corresponde al área dueña de la causa.")

        det_d = date.fromisoformat(case["detection_date"])
        max_imp_d = date.fromisoformat(case["max_implementation_date"])
        imp_d = _parse_iso_date(imp_str)
        ver_d = _parse_iso_date(ver_str)
        imp_ok = imp_d is not None and det_d <= imp_d <= max_imp_d
        if not imp_ok:
            reasons.append(
                f"Fecha de implementación inválida (debe estar entre {det_d} y {max_imp_d})."
            )

        lag = int(case.get("min_verification_lag_days", 1))
        ver_date_ok = (
            imp_d is not None and ver_d is not None and ver_d >= imp_d + timedelta(days=lag)
        )
        if not ver_date_ok:
            reasons.append(
                f"La verificación de eficacia debe realizarse al menos {lag} días "
                "después de implementar."
            )

        ver_ok = verif == case["expected_verification"]
        if not ver_ok:
            reasons.append("El criterio de verificación no comprueba que la causa fue eliminada.")

        doc_ok = (doc_chg is case["expected_doc_change"]) and (
            not case["expected_doc_change"] or aff_doc == case.get("expected_document")
        )
        if not doc_ok:
            reasons.append("Revisa si se requiere actualizar documentación y qué documento aplica.")

        checks = [corr_ok, root_ok, act_ok, resp_ok, imp_ok, ver_date_ok, ver_ok, doc_ok]
        ok = all(checks)
        earned += sum(checks) / len(checks)
        fb = (
            "Ficha de no conformidad correcta." if ok else " ".join([*reasons, case["explanation"]])
        )
        feedback_list.append(DocItemFeedback(cid, ok, fb))

    return DocGradeResult(_pct_float(earned, len(spec["cases"])), tuple(feedback_list))


def guide_nonconformity_form(spec: Spec, failed_ids: set[str]) -> list[SolutionGuideItem]:
    pos = _opt_labels(spec["positions"])
    docs = _opt_labels(spec["documents"])
    guides: list[SolutionGuideItem] = []
    for c in spec["cases"]:
        if c["id"] not in failed_ids:
            continue
        corr = _opt_labels(c["correction_options"]).get(c["expected_correction"], "")
        root = _opt_labels(c["root_cause_options"]).get(c["expected_root_cause"], "")
        act = _opt_labels(c["action_options"]).get(c["expected_action"], "")
        doc_txt = (
            docs.get(c.get("expected_document", ""), "")
            if c["expected_doc_change"]
            else "Sin cambio documental"
        )
        guides.append(
            SolutionGuideItem(
                c["id"],
                c["title"],
                f"Corrección: {corr} · Causa: {root} · Acción: {act} · "
                f"Responsable: {pos.get(c['expected_responsible'], '')} · "
                f"Verificación >= +{c.get('min_verification_lag_days', 1)} días · {doc_txt}.",
            )
        )
    return guides


# ----------------------------------------------------------------------------- competence_matrix


def validate_competence_matrix(spec: Spec) -> None:
    _need(bool(spec.get("scenario")), "falta `scenario`")
    comp_ids = _labelled_ids(spec.get("competencies"), "competencies")
    trn_ids = _labelled_ids(spec.get("trainings"), "trainings")
    ev_ids = _labelled_ids(spec.get("evidences"), "evidences")
    eval_ids = _labelled_ids(spec["evaluators"], "evaluators") if "evaluators" in spec else []
    rows = _list_of_dicts(spec.get("rows"), "rows")
    rids: list[str] = []
    for r in rows:
        rid = _req_id(r, "fila")
        _need(bool(r.get("position_title")), f"fila {rid}: falta `position_title`")
        _need(r.get("expected_competency") in comp_ids, f"fila {rid}: competencia invalida")
        _need(r.get("expected_training") in trn_ids, f"fila {rid}: capacitacion invalida")
        _need(r.get("expected_evidence") in ev_ids, f"fila {rid}: evidencia invalida")
        if eval_ids:
            valid_ev = r.get("valid_evaluators") or (
                [r["expected_evaluator"]] if r.get("expected_evaluator") else []
            )
            _need(
                bool(valid_ev) and all(x in eval_ids for x in valid_ev),
                f"fila {rid}: evaluador esperado invalido",
            )
        _need(bool(r.get("explanation")), f"fila {rid}: falta `explanation`")
        rids.append(rid)
    _need(len(set(rids)) == len(rids), "ids de fila repetidos")


def public_competence_matrix(spec: Spec, seed: str) -> Spec:
    out: dict[str, Any] = {
        "prompt": spec["prompt"],
        "scenario": spec["scenario"],
        "competencies": _shuffled_opts(spec["competencies"], f"{seed}:comp"),
        "trainings": _strip_opts(spec["trainings"]),
        "evidences": _shuffled_opts(spec["evidences"], f"{seed}:ev"),
        "rows": [
            {
                "id": r["id"],
                "position_title": r["position_title"],
                "role_summary": r.get("role_summary", ""),
            }
            for r in spec["rows"]
        ],
    }
    if "evaluators" in spec:
        out["evaluators"] = _strip_opts(spec["evaluators"])
    return out


def grade_competence_matrix(spec: Spec, answer: Any) -> DocGradeResult:
    ans_rows = _expect_dict(answer, "rows")
    has_evaluators = "evaluators" in spec
    feedback_list: list[DocItemFeedback] = []
    earned = 0.0

    for row in spec["rows"]:
        rid = row["id"]
        raw = ans_rows.get(rid)
        if raw is not None and not isinstance(raw, dict):
            raise DocAnswerError(f"`rows.{rid}` debe ser un objeto")
        raw = raw or {}
        comp = _expect_str(raw, "competency_id")
        trn = _expect_str(raw, "training_id")
        ev = _expect_str(raw, "evidence_id")
        eval_id = _expect_str(raw, "evaluator_id") if has_evaluators else ""

        c_ok = comp == row["expected_competency"]
        t_ok = trn == row["expected_training"]
        e_ok = ev == row["expected_evidence"]

        reasons: list[str] = []
        if not c_ok:
            reasons.append(
                "La competencia asignada no corresponde a las responsabilidades del cargo."
            )
        if not t_ok:
            reasons.append("El nivel de capacitación elegido resulta insuficiente o inadecuado.")
        if not e_ok:
            reasons.append(
                "La evidencia seleccionada no acredita eficacia (asistencia ≠ competencia)."
            )

        checks = [c_ok, t_ok, e_ok]
        if has_evaluators:
            valid_evals = row.get("valid_evaluators") or [row["expected_evaluator"]]
            forb_evals = set(row.get("forbidden_evaluators", []))
            ev_ok = eval_id in valid_evals and eval_id not in forb_evals
            if eval_id in forb_evals:
                reasons.append(
                    "Conflicto de interés: el cargo no puede autoevaluar su competencia."
                )
            elif not ev_ok:
                reasons.append("Evaluador sin competencia técnica o autoridad para este rol.")
            checks.append(ev_ok)

        ok = all(checks)
        earned += sum(checks) / len(checks)
        fb = (
            "Competencia y evidencia correctas." if ok else " ".join([*reasons, row["explanation"]])
        )
        feedback_list.append(DocItemFeedback(rid, ok, fb))

    return DocGradeResult(_pct_float(earned, len(spec["rows"])), tuple(feedback_list))


def guide_competence_matrix(spec: Spec, failed_ids: set[str]) -> list[SolutionGuideItem]:
    comps = _opt_labels(spec["competencies"])
    trns = _opt_labels(spec["trainings"])
    evs = _opt_labels(spec["evidences"])
    evals = _opt_labels(spec.get("evaluators", []))
    guides: list[SolutionGuideItem] = []
    for r in spec["rows"]:
        if r["id"] not in failed_ids:
            continue
        eval_part = ""
        if "evaluators" in spec:
            ev_id = r.get("expected_evaluator") or (r.get("valid_evaluators") or [""])[0]
            eval_part = f" · Evaluador: {evals.get(ev_id, ev_id)}"
        guides.append(
            SolutionGuideItem(
                r["id"],
                r["position_title"],
                f"Competencia: {comps.get(r['expected_competency'], '')} · "
                f"Capacitación: {trns.get(r['expected_training'], '')} · "
                f"Evidencia: {evs.get(r['expected_evidence'], '')}{eval_part}.",
            )
        )
    return guides
