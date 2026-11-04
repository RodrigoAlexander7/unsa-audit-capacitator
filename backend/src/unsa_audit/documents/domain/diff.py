"""Normalizacion, hash y diff de documentos Markdown (puros)."""

import difflib
import hashlib
from dataclasses import dataclass, field
from typing import Literal

LineKind = Literal["add", "del", "ctx"]


def normalize_content(text: str) -> str:
    """Unifica saltos de linea, quita espacios finales y lineas en blanco de los extremos."""
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    body = "\n".join(lines).strip("\n")
    return body + "\n" if body else ""


def content_hash(text: str) -> str:
    return hashlib.sha256(normalize_content(text).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class DiffLine:
    kind: LineKind
    old_line: int | None
    new_line: int | None
    text: str


@dataclass(frozen=True)
class Hunk:
    old_start: int
    new_start: int
    lines: list[DiffLine] = field(default_factory=list)


@dataclass(frozen=True)
class Diff:
    hunks: list[Hunk]
    additions: int
    deletions: int


def compute_diff(old: str, new: str, context: int = 3) -> Diff:
    """Diff por lineas entre dos textos (se comparan ya normalizados)."""
    old_lines = normalize_content(old).splitlines()
    new_lines = normalize_content(new).splitlines()
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False)

    hunks: list[Hunk] = []
    additions = deletions = 0
    for group in matcher.get_grouped_opcodes(context):
        lines: list[DiffLine] = []
        for tag, i1, i2, j1, j2 in group:
            if tag == "equal":
                lines += [
                    DiffLine("ctx", i + 1, j + 1, old_lines[i])
                    for i, j in zip(range(i1, i2), range(j1, j2), strict=True)
                ]
                continue
            if tag in ("replace", "delete"):
                lines += [DiffLine("del", i + 1, None, old_lines[i]) for i in range(i1, i2)]
                deletions += i2 - i1
            if tag in ("replace", "insert"):
                lines += [DiffLine("add", None, j + 1, new_lines[j]) for j in range(j1, j2)]
                additions += j2 - j1
        hunks.append(Hunk(group[0][1] + 1, group[0][3] + 1, lines))
    return Diff(hunks, additions, deletions)
