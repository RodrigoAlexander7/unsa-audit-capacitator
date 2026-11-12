"""Reglas puras de validacion, anti-inyeccion y prevencion de fuga de soluciones."""

import hashlib
import json
import re
import unicodedata
from typing import Any

from unsa_audit.assistant.domain.entities import (
    MAX_ASSISTANT_QUESTION_CHARS,
    MAX_LESSON_EXCERPT_CHARS,
    MAX_REFERENCE_EXCERPT_CHARS,
    MAX_ROUTE_PATH_CHARS,
    PromptContext,
)

_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(ignora|olvida|omite|descarta)\b.{0,30}\b(instruccion|regla|system|prompt)",
        re.I,
    ),
    re.compile(
        r"\bignore\b.{0,30}\b(previous|all|system)\b.{0,20}\b(instruction|rule|prompt)",
        re.I,
    ),
    re.compile(r"\b(system\s*prompt|prompt\s+del\s+sistema|instrucciones\s+internas)\b", re.I),
    re.compile(r"\b(jailbreak|modo\s+desarrollador|developer\s+mode|dan\s+mode)\b", re.I),
    re.compile(
        r"\b(devuelve|imprime|muestra|dame)\b.{0,25}"
        r"\b(json\s+crudo|el\s+contexto\s+completo|tu\s+prompt)\b",
        re.I,
    ),
    re.compile(r"</?\s*(contexto|pregunta_estudiante|reglas|system)\b", re.I),
)

_CHEATING_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(dame|pasa|pasame|envia|revela|muestra|indica|dime)\b.{0,30}\b"
        r"(la|las|los)?\s*(respuesta|respuestas|solucion|soluciones|clave|claves|veredicto|veredictos)\b"
        r".{0,25}\b(exacta|exactas|correcta|correctas|del\s+ejercicio|para\s+aprobar|para\s+pasar)?",
        re.I,
    ),
    re.compile(
        r"\b(cual|cuales)\s+(es|son)\s+(la|las)\s+(respuesta|respuestas|opcion|opciones|claves)\s+"
        r"(correcta|correctas|para\s+aprobar)",
        re.I,
    ),
    re.compile(
        r"\b(resuelve|completa|llena|haz)\b.{0,25}\b"
        r"(por\s+mi|el\s+ejercicio|este\s+ejercicio|el\s+formulario|la\s+tabla)\b",
        re.I,
    ),
    re.compile(
        r"\bque\s+(pongo|escribo|marco|selecciono)\s+en\s+"
        r"(cada|todos\s+los)\s+(campo|campos|fila|filas)\b",
        re.I,
    ),
    re.compile(r"\b(give\s+me\s+the\s+(exact\s+)?answers?|solve\s+(the\s+)?exercise)\b", re.I),
)

REFUSAL_INJECTION = (
    "No puedo modificar mis reglas ni mostrar instrucciones internas del sistema. "
    "Con gusto te ayudo a entender los requisitos ISO/IEC 27701, ISO 19011 o la "
    "organización ficticia de la UNSA."
)

REFUSAL_SOLUTION = (
    "No puedo darte respuestas exactas ni completar ejercicios por ti, porque la evaluación "
    "mide tu criterio como auditor o implementador. Puedo explicarte la cláusula aplicable, "
    "el propósito del documento y cómo analizar los datos de la UNSA para tomar tu decisión."
)


class QuestionValidationError(ValueError):
    """Error puro al validar la entrada del usuario."""


def _fold_accents(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def sanitize_question(raw: str) -> str:
    """Limpia controles y valida longitud no vacia; lanza QuestionValidationError si es invalida."""
    if not isinstance(raw, str):
        raise QuestionValidationError("Pregunta inválida")
    cleaned = _CONTROL_RE.sub("", raw).strip()
    if not cleaned or len(cleaned) > MAX_ASSISTANT_QUESTION_CHARS:
        raise QuestionValidationError("La pregunta debe tener entre 1 y 800 caracteres.")
    return cleaned


def sanitize_route_path(raw: str | None) -> str | None:
    if raw is None:
        return None
    cleaned = _CONTROL_RE.sub("", raw).strip()
    if not cleaned:
        return None
    if len(cleaned) > MAX_ROUTE_PATH_CHARS:
        return cleaned[:MAX_ROUTE_PATH_CHARS]
    return cleaned


def truncate_excerpt(text: str | None, limit: int) -> str | None:
    if not text:
        return None
    clean = _CONTROL_RE.sub("", text).strip()
    if len(clean) <= limit:
        return clean
    cut = clean[:limit].rsplit(" ", 1)[0].strip()
    return f"{cut}..."


def detect_guardrail_refusal(question: str, *, has_exercise: bool = False) -> str | None:
    """Devuelve mensaje de rechazo pedagogico si detecta inyeccion o pedido de respuestas."""
    folded = _fold_accents(question)
    if any(pattern.search(folded) for pattern in _INJECTION_PATTERNS):
        return REFUSAL_INJECTION
    if any(pattern.search(folded) for pattern in _CHEATING_PATTERNS):
        folded_low = folded.lower()
        cheating_hint = any(w in folded_low for w in ("ejercicio", "aprobar", "clave", "respuesta"))
        if has_exercise or cheating_hint:
            return REFUSAL_SOLUTION
    return None


def _escape_untrusted_text(text: str) -> str:
    """Neutraliza delimitadores y cercas markdown antes de embeber entrada en prompt."""
    return text.replace("```", "'''").replace("<", "‹").replace(">", "›")


def _context_payload(ctx: PromptContext) -> dict[str, Any]:
    return {
        "pagina_actual": {
            "ruta_web": ctx.route_path,
            "ruta_formativa": ctx.route_title,
            "modulo_actual": ctx.module_title,
            "tiene_ejercicio": ctx.has_exercise,
            "extracto_leccion": truncate_excerpt(ctx.lesson_excerpt, MAX_LESSON_EXCERPT_CHARS),
            "extracto_referencia": truncate_excerpt(
                ctx.reference_excerpt, MAX_REFERENCE_EXCERPT_CHARS
            ),
        },
        "unsa_ficticia": {
            "unidades": list(ctx.unsa_units),
            "cargos": list(ctx.unsa_positions),
            "sistemas": list(ctx.unsa_systems),
            "actividades_tratamiento": list(ctx.unsa_activities),
        },
        "estado_pims": list(ctx.pims_docs),
    }


def compute_context_hash(ctx: PromptContext) -> str:
    canonical = json.dumps(_context_payload(ctx), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_student_prompt(system_prompt: str, ctx: PromptContext, question: str) -> tuple[str, str]:
    """Construye prompt acotado + hash del contexto, aislando entrada como datos no confiables."""
    payload = _context_payload(ctx)
    ctx_hash = compute_context_hash(ctx)
    data = json.dumps(payload, ensure_ascii=False, indent=1)
    safe_q = _escape_untrusted_text(question)
    prompt = (
        f"{system_prompt.strip()}\n\n"
        f"<CONTEXTO>\n{data}\n</CONTEXTO>\n\n"
        f"<PREGUNTA_ESTUDIANTE>\n{safe_q}\n</PREGUNTA_ESTUDIANTE>"
    )
    return prompt, ctx_hash


def filter_model_output(raw: str) -> str:
    """Limpia etiquetas de delimitacion internas y recorta salidas desbordadas."""
    cleaned = raw.replace("<CONTEXTO>", "").replace("</CONTEXTO>", "")
    cleaned = cleaned.replace("<PREGUNTA_ESTUDIANTE>", "").replace("</PREGUNTA_ESTUDIANTE>", "")
    cleaned = cleaned.strip()
    if len(cleaned) > 6000:
        cleaned = f"{cleaned[:6000].rstrip()}\n\n[Respuesta resumida por longitud]"
    return cleaned
