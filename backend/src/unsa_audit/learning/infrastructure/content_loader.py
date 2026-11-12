"""Lee `content/routes/<ruta>/` y lo convierte en rutas y modulos del dominio.

Estructura:
    route.yaml                 code, order, title, description, hours, prerequisite
    NN-slug.md                 frontmatter (title, minutes, mandatory, final) + leccion Markdown
    NN-slug.exercise.json      kind, pass_score, spec | (generator + params)
"""

import json
import re
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

import yaml

from unsa_audit.learning.application.generators import GENERATORS
from unsa_audit.learning.domain.exercises import InvalidExerciseSpec, validate_spec
from unsa_audit.learning.domain.route import (
    DEFAULT_PASS_SCORE,
    ExerciseDef,
    ExerciseKind,
    Module,
    Route,
)

_NS = uuid5(NAMESPACE_URL, "https://unsa-audit-poc.example/content")
_MODULE_FILE = re.compile(r"^(?P<order>\d{2})-(?P<slug>[a-z0-9-]+)\.md$")
_VERSION_FILE = re.compile(r"^v(?P<number>\d+)\.md$")
_FRONTMATTER = re.compile(r"\A---\n(?P<meta>.*?)\n---\n(?P<body>.*)\Z", re.DOTALL)


class ContentError(ValueError):
    """El contenido del repositorio esta mal formado."""


def module_id(route_code: str, slug: str) -> UUID:
    return uuid5(_NS, f"module:{route_code}:{slug}")


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ContentError(f"{path}: se esperaba un mapa YAML")
    return data


def _load_exercise(path: Path) -> ExerciseDef:
    raw = json.loads(path.read_text(encoding="utf-8"))
    try:
        kind = ExerciseKind(raw["kind"])
    except (KeyError, ValueError) as exc:
        raise ContentError(f"{path}: `kind` invalido") from exc
    generator = raw.get("generator")
    spec = raw.get("spec", {})
    try:
        if generator:
            if generator not in GENERATORS:
                raise InvalidExerciseSpec(f"generador desconocido: {generator}")
        else:
            validate_spec(kind, spec)
    except InvalidExerciseSpec as exc:
        raise ContentError(f"{path}: {exc}") from exc
    return ExerciseDef(
        kind=kind,
        spec=spec,
        generator=generator,
        params=raw.get("params", {}),
        pass_score=int(raw.get("pass_score", DEFAULT_PASS_SCORE)),
    )


def _load_reference(
    content_dir: Path, md_path: Path, ref_doc: str | None
) -> tuple[str | None, str | None]:
    if ref_doc:
        doc_dir = content_dir / "institutional" / ref_doc
        doc_yaml = doc_dir / "document.yaml"
        if not doc_dir.is_dir() or not doc_yaml.exists():
            raise ContentError(f"{md_path}: `reference_doc` inexistente ({ref_doc})")
        doc_meta = _read_yaml(doc_yaml)
        versions = {
            int(m["number"]): p for p in doc_dir.glob("v*.md") if (m := _VERSION_FILE.match(p.name))
        }
        if not versions:
            raise ContentError(f"{md_path}: `reference_doc` sin versiones ({ref_doc})")
        latest = versions[max(versions)]
        parsed = _FRONTMATTER.match(latest.read_text(encoding="utf-8"))
        body = (parsed["body"] if parsed else latest.read_text(encoding="utf-8")).strip()
        return str(doc_meta.get("title", ref_doc)), body

    sidecar = md_path.with_name(f"{md_path.stem}.reference.md")
    if not sidecar.exists():
        return None, None
    raw = sidecar.read_text(encoding="utf-8")
    parsed = _FRONTMATTER.match(raw)
    if parsed:
        meta = yaml.safe_load(parsed["meta"]) or {}
        body = parsed["body"].strip()
        title = str(meta.get("title") or "Ejemplo resuelto (UNSA)")
    else:
        body = raw.strip()
        first_h = next((ln[2:].strip() for ln in body.splitlines() if ln.startswith("# ")), "")
        title = first_h or "Ejemplo resuelto (UNSA)"
    if not body:
        raise ContentError(f"{sidecar}: ejemplo de referencia vacio")
    return title, body


def _load_module(content_dir: Path, route_code: str, md_path: Path) -> Module:
    match = _MODULE_FILE.match(md_path.name)
    if match is None:
        raise ContentError(f"{md_path}: el nombre debe ser NN-slug.md")
    parsed = _FRONTMATTER.match(md_path.read_text(encoding="utf-8"))
    if parsed is None:
        raise ContentError(f"{md_path}: falta el frontmatter YAML")
    meta = yaml.safe_load(parsed["meta"]) or {}
    if not meta.get("title") or not isinstance(meta.get("minutes"), int):
        raise ContentError(f"{md_path}: el frontmatter necesita `title` y `minutes` (entero)")
    exercise_path = md_path.with_name(f"{md_path.stem}.exercise.json")
    slug = match["slug"]
    planned = bool(meta.get("planned", False))
    exercise = _load_exercise(exercise_path) if exercise_path.exists() else None
    if planned and (exercise is not None or meta.get("mandatory", False)):
        raise ContentError(
            f"{md_path}: un modulo `planned` no puede ser obligatorio ni tener ejercicio"
        )
    ref_doc = meta.get("reference_doc")
    ref_title, ref_md = _load_reference(content_dir, md_path, str(ref_doc) if ref_doc else None)
    return Module(
        id=module_id(route_code, slug),
        route_code=route_code,
        slug=slug,
        order=int(match["order"]),
        title=str(meta["title"]),
        minutes=meta["minutes"],
        mandatory=False if planned else bool(meta.get("mandatory", True)),
        is_final=bool(meta.get("final", False)),
        lesson_md=parsed["body"].strip(),
        exercise=exercise,
        planned=planned,
        reference_title=ref_title,
        reference_md=ref_md,
    )


class FileContentSource:
    def __init__(self, content_dir: Path) -> None:
        self._content_dir = content_dir
        self._routes_dir = content_dir / "routes"

    def load(self) -> tuple[list[Route], list[Module]]:
        routes: list[Route] = []
        modules: list[Module] = []
        for route_dir in sorted(p for p in self._routes_dir.iterdir() if p.is_dir()):
            meta = _read_yaml(route_dir / "route.yaml")
            try:
                route = Route(
                    code=meta["code"],
                    order=int(meta["order"]),
                    title=meta["title"],
                    description=str(meta.get("description", "")).strip(),
                    hours=int(meta["hours"]),
                    prerequisite_code=meta.get("prerequisite"),
                )
            except KeyError as exc:
                raise ContentError(f"{route_dir}/route.yaml: falta {exc}") from exc
            routes.append(route)
            mod_files = [
                p for p in sorted(route_dir.glob("*.md")) if not p.name.endswith(".reference.md")
            ]
            modules += [_load_module(self._content_dir, route.code, p) for p in mod_files]

        codes = {r.code for r in routes}
        for route in routes:
            if route.prerequisite_code and route.prerequisite_code not in codes:
                raise ContentError(f"{route.code}: prerrequisito inexistente")
        return routes, modules
