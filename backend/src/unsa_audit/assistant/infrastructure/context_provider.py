"""Proveedor de contextoUNSA + leccion/documento (sin PII ni soluciones de ejercicios)."""

from uuid import UUID

from unsa_audit.assistant.domain.entities import (
    MAX_LESSON_EXCERPT_CHARS,
    MAX_REFERENCE_EXCERPT_CHARS,
    PromptContext,
)
from unsa_audit.assistant.domain.guardrails import truncate_excerpt
from unsa_audit.documents.application.ports import DocumentRepository
from unsa_audit.learning.application.ports import LearningRepository, UniversityFacts


class PlatformStudentContextProvider:
    """Construye PromptContext sin acceder nunca a `.exercise` ni a cuentas de usuario."""

    def __init__(
        self,
        facts: UniversityFacts,
        learning: LearningRepository,
        documents: DocumentRepository,
    ) -> None:
        self._facts = facts
        self._learning = learning
        self._documents = documents

    async def build(self, module_id: UUID | None, route_path: str | None) -> PromptContext:
        snapshot = await self._facts.snapshot()
        route_title: str | None = None
        module_title: str | None = None
        has_exercise = False
        lesson_excerpt: str | None = None
        reference_excerpt: str | None = None

        if module_id is not None:
            mod = await self._learning.get_module(module_id)
            if mod is not None and not mod.planned:
                module_title = mod.title
                has_exercise = mod.exercise is not None
                lesson_excerpt = truncate_excerpt(mod.lesson_md, MAX_LESSON_EXCERPT_CHARS)
                reference_excerpt = truncate_excerpt(mod.reference_md, MAX_REFERENCE_EXCERPT_CHARS)
                route = await self._learning.get_route(mod.route_code)
                if route is not None:
                    route_title = route.title
        elif route_path:
            segments = [s for s in route_path.split("/") if s]
            if len(segments) >= 2 and segments[0] == "routes":
                route = await self._learning.get_route(segments[1])
                if route is not None:
                    route_title = route.title
            elif len(segments) >= 2 and segments[0] == "documents" and segments[1] != "pims":
                summary = await self._documents.get_summary(segments[1])
                if summary is not None:
                    version = await self._documents.get_version(
                        summary.document.id, summary.current_number
                    )
                    module_title = summary.document.title
                    if version is not None:
                        reference_excerpt = truncate_excerpt(
                            version.content_md, MAX_REFERENCE_EXCERPT_CHARS
                        )

        return PromptContext(
            route_path=route_path,
            route_title=route_title,
            module_id=module_id,
            module_title=module_title,
            has_exercise=has_exercise,
            lesson_excerpt=lesson_excerpt,
            reference_excerpt=reference_excerpt,
            unsa_units=tuple(
                {"code": u.code, "name": u.name, "kind": u.kind} for u in snapshot.units
            ),
            unsa_positions=tuple(
                {"title": p.title, "unit": p.unit_name or p.unit_kind} for p in snapshot.positions
            ),
            unsa_systems=tuple(
                {
                    "name": s.name,
                    "owner_unit": s.owner_unit_name,
                    "data_categories": list(s.data_categories),
                }
                for s in snapshot.systems
            ),
            unsa_activities=tuple(
                {
                    "name": a.name,
                    "unit": a.org_unit_name,
                    "purpose": a.purpose,
                    "legal_basis": a.legal_basis,
                    "retention": a.retention,
                }
                for a in snapshot.activities
            ),
            pims_docs=tuple(
                {
                    "code": p.code,
                    "clause": p.clause_ref,
                    "title": p.title,
                    "state": p.state,
                    "owner_unit": p.owner_unit_name,
                }
                for p in snapshot.pims
            ),
        )
