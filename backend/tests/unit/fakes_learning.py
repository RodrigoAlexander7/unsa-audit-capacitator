from datetime import date
from pathlib import Path
from uuid import UUID

from unsa_audit.documents.domain.pims import evaluate_state
from unsa_audit.documents.infrastructure.content_loader import (
    FileDocumentSource,
    FilePimsRequirementSource,
)
from unsa_audit.learning.application.ports import (
    ActivityFact,
    PimsFact,
    PositionFact,
    SystemFact,
    UnitFact,
    UniversitySnapshot,
)
from unsa_audit.learning.domain.route import (
    Enrollment,
    ExerciseAttempt,
    Module,
    ModuleProgress,
    Route,
)
from unsa_audit.seed.university_data import UniversityDataset, build_university_dataset

CONTENT = Path(__file__).resolve().parents[3] / "content"


def pims_facts(today: date = date(2026, 11, 11)) -> list[PimsFact]:
    """Estado del conjunto PIMS sembrado (requisitos + documentos reales) a una fecha."""
    requirements = FilePimsRequirementSource(CONTENT).load()
    seeds = {s.document.kind: s.document for s in FileDocumentSource(CONTENT).load()}
    names = {u.code: u.name for u in build_university_dataset().org_units}
    facts: list[PimsFact] = []
    for r in requirements:
        doc = seeds.get(r.document_kind)
        evaluation = evaluate_state(
            exists=doc is not None,
            lifecycle=doc.lifecycle if doc else None,
            review_date=doc.review_date if doc else None,
            owner_unit_code=doc.owner_unit_code if doc else None,
            today=today,
        )
        facts.append(
            PimsFact(
                r.code,
                r.clause_ref,
                r.title,
                evaluation.state.value,
                doc.title if doc else None,
                1 if doc else None,
                doc.review_date if doc else None,
                names.get(doc.owner_unit_code or "") if doc else None,
                expected_evidence=r.expected_evidence,
                summary=r.summary,
            )
        )
    return facts


def snapshot_from_dataset(ds: UniversityDataset | None = None) -> UniversitySnapshot:
    ds = ds or build_university_dataset()
    units = {u.id: u for u in ds.org_units}
    positions = {p.id: p for p in ds.positions}
    return UniversitySnapshot(
        units=[UnitFact(u.code, u.name, u.kind.value) for u in ds.org_units],
        positions=[
            PositionFact(
                p.title,
                units[p.org_unit_id].kind.value,
                units[p.org_unit_id].code,
                units[p.org_unit_id].name,
            )
            for p in positions.values()
        ],
        systems=[
            SystemFact(
                s.name,
                units[s.owner_org_unit_id].name,
                units[s.owner_org_unit_id].code,
                s.data_categories,
            )
            for s in ds.systems
        ],
        pims=pims_facts(),
        activities=[
            ActivityFact(
                a.name,
                units[a.org_unit_id].code,
                units[a.org_unit_id].name,
                a.purpose,
                a.legal_basis,
                a.data_categories,
                a.retention,
            )
            for a in ds.processing_activities
        ],
    )


class FakeFacts:
    def __init__(self, snapshot: UniversitySnapshot | None = None) -> None:
        self._snapshot = snapshot or snapshot_from_dataset()

    async def snapshot(self) -> UniversitySnapshot:
        return self._snapshot


class InMemoryLearningRepository:
    def __init__(self, routes: list[Route] | None = None, modules: list[Module] | None = None):
        self.routes = {r.code: r for r in routes or []}
        self.modules = {m.id: m for m in modules or []}
        self.enrollments: dict[tuple[UUID, str], Enrollment] = {}
        self.progress: dict[tuple[UUID, UUID], ModuleProgress] = {}
        self.attempts: list[ExerciseAttempt] = []

    async def replace_content(self, routes: list[Route], modules: list[Module]) -> None:
        self.routes = {r.code: r for r in routes}
        self.modules = {m.id: m for m in modules}

    async def list_routes(self) -> list[Route]:
        return sorted(self.routes.values(), key=lambda r: r.order)

    async def get_route(self, code: str) -> Route | None:
        return self.routes.get(code)

    async def list_modules(self, route_code: str | None = None) -> list[Module]:
        mods = [m for m in self.modules.values() if route_code in (None, m.route_code)]
        return sorted(mods, key=lambda m: (m.route_code, m.order))

    async def get_module(self, module_id: UUID) -> Module | None:
        return self.modules.get(module_id)

    async def get_enrollment(self, user_id: UUID, route_code: str) -> Enrollment | None:
        return self.enrollments.get((user_id, route_code))

    async def list_enrollments(self, user_id: UUID) -> list[Enrollment]:
        return [e for (uid, _), e in self.enrollments.items() if uid == user_id]

    async def save_enrollment(self, enrollment: Enrollment) -> None:
        self.enrollments[(enrollment.user_id, enrollment.route_code)] = enrollment

    async def list_progress(self, user_id: UUID) -> dict[UUID, ModuleProgress]:
        return {mid: p for (uid, mid), p in self.progress.items() if uid == user_id}

    async def save_progress(self, progress: ModuleProgress) -> None:
        self.progress[(progress.user_id, progress.module_id)] = progress

    async def add_attempt(self, attempt: ExerciseAttempt) -> None:
        self.attempts.append(attempt)

    async def count_attempts(self, user_id: UUID, module_id: UUID) -> int:
        return sum(1 for a in self.attempts if a.user_id == user_id and a.module_id == module_id)
