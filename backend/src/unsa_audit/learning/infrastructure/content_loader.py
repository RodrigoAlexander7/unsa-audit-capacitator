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


def _load_module(route_code: str, md_path: Path) -> Module:
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
    return Module(
        id=module_id(route_code, slug),
        route_code=route_code,
        slug=slug,
        order=int(match["order"]),
        title=str(meta["title"]),
        minutes=meta["minutes"],
        mandatory=bool(meta.get("mandatory", True)),
        is_final=bool(meta.get("final", False)),
        lesson_md=parsed["body"].strip(),
        exercise=_load_exercise(exercise_path) if exercise_path.exists() else None,
    )


class FileContentSource:
    def __init__(self, content_dir: Path) -> None:
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
            modules += [_load_module(route.code, p) for p in sorted(route_dir.glob("*.md"))]

        codes = {r.code for r in routes}
        for route in routes:
            if route.prerequisite_code and route.prerequisite_code not in codes:
                raise ContentError(f"{route.code}: prerrequisito inexistente")
        return routes, modules
