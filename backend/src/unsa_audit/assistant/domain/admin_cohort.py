"""Reglas puras de seudonimizacion del cohorte y parseo de propuestas."""

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class ProposalStatus(StrEnum):
    DRAFT = "draft"
    ACCEPTED = "accepted"
    DISCARDED = "discarded"


VALID_CHANGE_TYPES = frozenset(
    {
        "reorder",
        "split",
        "reinforce",
        "update_minutes",
        "add_practice",
        "review_prerequisite",
    }
)


@dataclass(frozen=True)
class LearnerAliasRecord:
    """Registro interno del backend con identidad real + metricas (nunca enviado completo a IA)."""

    user_id: UUID
    alias: str
    full_name: str
    email: str
    stalled: bool
    days_since_activity: int | None
    overall_progress_pct: int
    minutes_credited: int
    attempts: int
    failed_attempts: int
    routes: tuple[dict[str, object], ...] = ()
    assessments: tuple[dict[str, object], ...] = ()

    def to_prompt_dict(self) -> dict[str, Any]:
        """Representacion estrictamente seudonima (sin nombres, correos ni UUID)."""
        return {
            "alias": self.alias,
            "stalled": self.stalled,
            "days_since_activity": self.days_since_activity,
            "overall_progress_pct": self.overall_progress_pct,
            "minutes_credited": self.minutes_credited,
            "attempts": self.attempts,
            "failed_attempts": self.failed_attempts,
            "routes": list(self.routes),
            "assessments": list(self.assessments),
        }

    def to_alias_info(self) -> dict[str, Any]:
        """Tabla de resolucion local devuelta solo al superadministrador autenticado."""
        return {
            "alias": self.alias,
            "full_name": self.full_name,
            "email": self.email,
            "stalled": self.stalled,
            "overall_progress_pct": self.overall_progress_pct,
        }


@dataclass(frozen=True)
class AdminCohortSnapshot:
    learners: tuple[LearnerAliasRecord, ...]
    routes_summary: tuple[dict[str, Any], ...]
    hard_modules: tuple[dict[str, Any], ...]
    pims_summary: dict[str, Any]
    valid_route_codes: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class CurriculumProposal:
    id: UUID
    created_by: UUID | None
    title: str
    target_route_code: str | None
    target_module_slug: str | None
    change_type: str
    proposed_change: str
    rationale: str
    evidence_metrics: dict[str, Any]
    status: str
    review_note: str | None
    context_hash: str
    created_at: datetime
    reviewed_at: datetime | None = None


class ProposalParseError(ValueError):
    """Error al interpretar la propuesta estructurada devuelta por el modelo."""


_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")


def _fold(value: str) -> str:
    nfkd = unicodedata.normalize("NFKD", value)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def pseudonymize_admin_question(question: str, learners: tuple[LearnerAliasRecord, ...]) -> str:
    """Reemplaza correos y nombres reales mencionados por el coordinador por sus alias P-xx."""
    result = question
    replacements: list[tuple[str, str]] = []
    for learner in learners:
        if learner.email:
            replacements.append((learner.email, learner.alias))
        if learner.full_name:
            replacements.append((learner.full_name, learner.alias))
    replacements.sort(key=lambda item: len(item[0]), reverse=True)

    for needle, alias in replacements:
        folded_needle = _fold(needle)
        if not folded_needle:
            continue
        # Busqueda insensible a mayusculas y tildes manteniendo alineacion aproximada por tokens
        pattern = re.compile(re.escape(needle), re.IGNORECASE)
        if pattern.search(result):
            result = pattern.sub(alias, result)
            continue
        # Fallback con texto normalizado sin tildes
        parts = needle.split()
        if len(parts) >= 2:
            flex = r"\s+".join(
                "".join(
                    f"[{re.escape(ch)}áéíóúÁÉÍÓÚñÑ]" if ch in "aeioun" else re.escape(ch)
                    for ch in _fold(p)
                )
                for p in parts
            )
            result = re.sub(flex, alias, result, flags=re.IGNORECASE)

    # Salvaguarda adicional: cualquier correo remanente no coincide con alias -> redactado
    result = _EMAIL_RE.sub("[correo-omitido]", result)
    return result


def build_cohort_payload(snapshot: AdminCohortSnapshot) -> dict[str, Any]:
    return {
        "total_participantes": len(snapshot.learners),
        "estancados": sum(1 for lr in snapshot.learners if lr.stalled),
        "participantes": [lr.to_prompt_dict() for lr in snapshot.learners],
        "rutas": list(snapshot.routes_summary),
        "modulos_dificiles": list(snapshot.hard_modules),
        "pims": snapshot.pims_summary,
    }


def compute_admin_context_hash(snapshot: AdminCohortSnapshot) -> str:
    canonical = json.dumps(build_cohort_payload(snapshot), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_admin_cohort_prompt(
    system_prompt: str, snapshot: AdminCohortSnapshot, safe_question: str
) -> tuple[str, str]:
    payload = build_cohort_payload(snapshot)
    ctx_hash = compute_admin_context_hash(snapshot)
    data = json.dumps(payload, ensure_ascii=False, indent=1)
    escaped_q = safe_question.replace("```", "'''").replace("<", "‹").replace(">", "›")
    prompt = (
        f"{system_prompt.strip()}\n\n"
        f"<CONTEXTO_COHORTE>\n{data}\n</CONTEXTO_COHORTE>\n\n"
        f"<PREGUNTA_ADMIN>\n{escaped_q}\n</PREGUNTA_ADMIN>"
    )
    return prompt, ctx_hash


def build_restructuring_prompt(
    system_prompt: str,
    snapshot: AdminCohortSnapshot,
    focus: str | None,
    route_code: str | None,
) -> tuple[str, str]:
    payload = build_cohort_payload(snapshot)
    ctx_hash = compute_admin_context_hash(snapshot)
    data = json.dumps(payload, ensure_ascii=False, indent=1)
    directive = {
        "enfoque_solicitado": focus
        or "Prioriza rutas con estancados o módulos con baja aprobación",
        "ruta_objetivo": route_code,
    }
    prompt = (
        f"{system_prompt.strip()}\n\n"
        f"<CONTEXTO_COHORTE>\n{data}\n</CONTEXTO_COHORTE>\n\n"
        f"<SOLICITUD>\n{json.dumps(directive, ensure_ascii=False)}\n</SOLICITUD>"
    )
    return prompt, ctx_hash


def _extract_json_block(raw_text: str) -> dict[str, Any]:
    text = raw_text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    candidate = fence.group(1) if fence else text
    if not candidate.startswith("{"):
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start != -1 and end > start:
            candidate = candidate[start : end + 1]
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ProposalParseError("La respuesta de la IA no contiene JSON válido.") from exc
    if not isinstance(parsed, dict):
        raise ProposalParseError("El JSON de propuestas debe ser un objeto.")
    return parsed


def parse_restructuring_proposals(
    raw_text: str,
    valid_route_codes: frozenset[str],
    *,
    created_by: UUID,
    context_hash: str,
    now: datetime,
    id_factory: Any,
) -> tuple[str, list[CurriculumProposal]]:
    parsed = _extract_json_block(raw_text)
    raw_items = parsed.get("proposals")
    if not isinstance(raw_items, list) or not raw_items:
        raise ProposalParseError("No se encontraron propuestas estructuradas en la respuesta.")

    summary = str(parsed.get("summary") or "Propuestas generadas a partir del cohorte.").strip()
    proposals: list[CurriculumProposal] = []
    for item in raw_items[:5]:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        proposed_change = str(item.get("proposed_change") or "").strip()
        rationale = str(item.get("rationale") or "").strip()
        if not (title and proposed_change and rationale):
            continue

        raw_route = item.get("target_route_code")
        target_route = (
            str(raw_route).strip()
            if isinstance(raw_route, str) and str(raw_route).strip() in valid_route_codes
            else None
        )
        raw_slug = item.get("target_module_slug")
        target_slug = (
            str(raw_slug).strip()[:120]
            if isinstance(raw_slug, str) and str(raw_slug).strip()
            else None
        )
        raw_type = str(item.get("change_type") or "reinforce").strip().lower()
        change_type = raw_type if raw_type in VALID_CHANGE_TYPES else "reinforce"
        metrics = item.get("evidence_metrics")
        evidence = metrics if isinstance(metrics, dict) else {}

        proposals.append(
            CurriculumProposal(
                id=id_factory(),
                created_by=created_by,
                title=title[:200],
                target_route_code=target_route,
                target_module_slug=target_slug,
                change_type=change_type,
                proposed_change=proposed_change,
                rationale=rationale,
                evidence_metrics=evidence,
                status=ProposalStatus.DRAFT.value,
                review_note=None,
                context_hash=context_hash,
                created_at=now,
                reviewed_at=None,
            )
        )

    if not proposals:
        raise ProposalParseError(
            "Ninguna propuesta contenía título, cambio y justificación válidos."
        )
    return summary, proposals
