"""Cohorte demo: participantes ficticios con avances variados.

Usa los casos de uso reales (registro, matricula, intentos, evaluaciones) con un reloj inyectado,
de modo que las estadisticas del panel son coherentes con las reglas del sistema.
Solo toca cuentas `@demo.unsa.example`; `--reset-demo` tambien elimina las de pruebas E2E.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from unsa_audit.assessment.application.use_cases import StartAssessment, SubmitAssessment
from unsa_audit.assessment.domain.assessment import Profile
from unsa_audit.assessment.infrastructure.question_bank import (
    FileQuestionBank,
    PimsRequirementCatalog,
)
from unsa_audit.assessment.infrastructure.sqlalchemy_repository import (
    SqlAlchemyAssessmentRepository,
)
from unsa_audit.core.config import Settings
from unsa_audit.documents.application.pims_use_cases import (
    GetPimsCompleteness,
    ListPimsRequirements,
)
from unsa_audit.documents.infrastructure.sqlalchemy_repository import (
    SqlAlchemyDocumentRepository,
    SqlAlchemyPimsRequirementRepository,
)
from unsa_audit.identity.application.use_cases import RegisterUser
from unsa_audit.identity.infrastructure.models import UserModel
from unsa_audit.identity.infrastructure.security import Argon2PasswordHasher
from unsa_audit.identity.infrastructure.sqlalchemy_user_repository import SqlAlchemyUserRepository
from unsa_audit.learning.application.generators import generate_spec
from unsa_audit.learning.application.use_cases import (
    CompleteReadingModule,
    EnrollInRoute,
    SubmitAttempt,
)
from unsa_audit.learning.domain.route import Module
from unsa_audit.learning.infrastructure.learning_facts import LearningFacts
from unsa_audit.learning.infrastructure.sqlalchemy_repository import SqlAlchemyLearningRepository
from unsa_audit.learning.infrastructure.sqlalchemy_university_facts import (
    SqlAlchemyUniversityFacts,
)
from unsa_audit.seed.solutions import solve, wrong

DEMO_DOMAIN = "demo.unsa.example"
E2E_DOMAIN = "e2e.unsa.example"
DEMO_PASSWORD = "Demo-1234"  # dato ficticio, solo POC

R1, R2, R3, R4 = "sensibilizacion", "interpretacion", "implementacion", "auditor"


@dataclass(frozen=True)
class Step:
    action: str  # enroll | pass | fail | pass_all | assess
    days_ago: float
    route: str = ""
    orders: tuple[int, ...] = ()
    times: int = 1
    profile: str = ""
    correct: int = 0


@dataclass(frozen=True)
class DemoLearner:
    slug: str
    name: str
    steps: tuple[Step, ...] = ()

    @property
    def email(self) -> str:
        return f"{self.slug}@{DEMO_DOMAIN}"


def enroll(route: str, days: float) -> Step:
    return Step("enroll", days, route=route)


def passes(route: str, days: float, *orders: int) -> Step:
    return Step("pass", days, route=route, orders=orders)


def fails(route: str, days: float, order: int, times: int = 1) -> Step:
    return Step("fail", days, route=route, orders=(order,), times=times)


def pass_all(route: str, days: float) -> Step:
    return Step("pass_all", days, route=route)


def assess(profile: str, days: float, correct: int) -> Step:
    return Step("assess", days, profile=profile, correct=correct)


COHORT: tuple[DemoLearner, ...] = (
    DemoLearner(
        "ana.quispe",
        "Ana Quispe Huamán",
        (
            enroll(R1, 7),
            pass_all(R1, 6),
            enroll(R2, 5),
            pass_all(R2, 4),
            enroll(R3, 3),
            pass_all(R3, 2),
            enroll(R4, 1),
            assess("controller", 1, 11),
        ),
    ),
    DemoLearner(
        "luis.mamani",
        "Luis Mamani Flores",
        (
            enroll(R1, 9),
            pass_all(R1, 8),
            enroll(R2, 7),
            pass_all(R2, 5),
            enroll(R3, 3),
            assess("controller", 4, 8),
        ),
    ),
    DemoLearner(
        "rosa.condori",
        "Rosa Condori Salas",
        (
            enroll(R1, 5),
            pass_all(R1, 4),
            assess("processor", 3, 10),
        ),
    ),
    DemoLearner(
        "jorge.caceres",
        "Jorge Cáceres Paredes",
        (
            enroll(R1, 9),
            passes(R1, 8, 1, 2, 3, 4, 5),
            fails(R1, 2, 6, times=2),
        ),
    ),
    DemoLearner(
        "lucia.valdivia",
        "Lucía Valdivia Ramos",
        (
            enroll(R1, 11),
            passes(R1, 11, 1, 2, 3),
            fails(R1, 10, 4, times=2),
        ),
    ),
    DemoLearner(
        "miguel.zuniga",
        "Miguel Zúñiga Cuadros",
        (
            enroll(R1, 3),
            passes(R1, 2, 1, 2),
        ),
    ),
    DemoLearner("elena.medina", "Elena Medina Arce", (enroll(R1, 14),)),
    DemoLearner(
        "pedro.bellido",
        "Pedro Bellido Choque",
        (
            enroll(R1, 6),
            passes(R1, 5, 1, 2, 3, 4, 5, 6),
            fails(R1, 1, 7),
        ),
    ),
    DemoLearner(
        "carmen.delgado",
        "Carmen Delgado Escobedo",
        (
            enroll(R1, 12),
            passes(R1, 12, 1, 2, 3, 4),
            assess("controller", 9, 5),
        ),
    ),
    DemoLearner("raul.fuentes", "Raúl Fuentes Gamarra"),
    DemoLearner(
        "silvia.herrera",
        "Silvia Herrera Lazo",
        (
            enroll(R1, 8),
            pass_all(R1, 7),
            enroll(R2, 6),
            assess("processor", 5, 4),
        ),
    ),
    DemoLearner(
        "andres.nunez",
        "Andrés Núñez Quispe",
        (
            enroll(R1, 2),
            passes(R1, 2, 1, 2, 3, 4, 5, 6),
        ),
    ),
)


@dataclass(frozen=True)
class DemoResult:
    created: int
    skipped: int
    removed: int


class _Services:
    """Casos de uso con repositorios reales y un reloj que se puede mover."""

    def __init__(self, sf: async_sessionmaker[AsyncSession], settings: Settings) -> None:
        self.users = SqlAlchemyUserRepository(sf)
        self.hasher = Argon2PasswordHasher()
        self.learning = SqlAlchemyLearningRepository(sf)
        documents = SqlAlchemyDocumentRepository(sf)
        pims_requirements = SqlAlchemyPimsRequirementRepository(sf)
        self.facts = LearningFacts(
            SqlAlchemyUniversityFacts(sf), GetPimsCompleteness(pims_requirements, documents)
        )
        self.assessments = SqlAlchemyAssessmentRepository(sf)
        self.bank = FileQuestionBank(settings.content_dir)
        self.catalog = PimsRequirementCatalog(ListPimsRequirements(pims_requirements))
        self.register = RegisterUser(self.users, self.hasher, settings.superadmin_email)

    async def modules(self, route: str) -> list[Module]:
        return [m for m in await self.learning.list_modules(route) if not m.planned]

    async def answer(self, module: Module, correct: bool) -> dict[str, Any]:
        exercise = module.exercise
        assert exercise is not None
        if not correct:
            return wrong(exercise.kind)
        if exercise.generator:
            spec = generate_spec(exercise.generator, exercise.params, await self.facts.snapshot())
        else:
            spec = exercise.spec
        return solve(exercise.kind, spec)


async def _run_step(services: _Services, user_id: UUID, step: Step, now: datetime) -> None:
    when = now - timedelta(days=step.days_ago)
    clock: Callable[[], datetime] = lambda: when  # noqa: E731

    if step.action == "enroll":
        await EnrollInRoute(services.learning, clock=clock).execute(user_id, step.route)
        return

    if step.action in ("pass", "fail", "pass_all"):
        modules = await services.modules(step.route)
        by_order = {m.order: m for m in modules}
        if step.action == "pass_all":  # la evaluacion final al ultimo
            ordered = sorted(modules, key=lambda m: (m.is_final, m.order))
        else:
            ordered = [by_order[o] for o in step.orders]
        submit = SubmitAttempt(services.learning, services.facts, clock=clock)
        reading = CompleteReadingModule(services.learning, clock=clock)
        for module in ordered:
            if module.exercise is None:  # lectura: solo se puede completar
                if step.action != "fail":
                    await reading.execute(user_id, module.id)
                continue
            repeats = step.times if step.action == "fail" else 1
            for _ in range(repeats):
                answer = await services.answer(module, correct=step.action != "fail")
                await submit.execute(user_id, module.id, answer)
        return

    if step.action == "assess":
        profile = Profile(step.profile)
        definition = services.bank.get(profile)
        assert definition is not None
        view = await StartAssessment(services.bank, services.assessments, clock=clock).execute(
            user_id, profile
        )
        truth = {q.id: q for q in definition.questions}
        answers: dict[str, str] = {}
        for index, qid in enumerate(view.attempt.question_ids):
            question = truth[qid]
            if index < step.correct:
                answers[qid] = question.correct
            else:
                answers[qid] = next(o.id for o in question.options if o.id != question.correct)
        await SubmitAssessment(
            services.bank, services.assessments, services.catalog, clock
        ).execute(user_id, view.attempt.id, answers)
        return

    raise ValueError(f"accion desconocida: {step.action}")


async def remove_demo_accounts(sf: async_sessionmaker[AsyncSession]) -> int:
    """Elimina las cuentas demo y E2E (el progreso cae en cascada)."""
    async with sf() as session, session.begin():
        result = await session.execute(
            delete(UserModel)
            .where(
                UserModel.email.like(f"%@{DEMO_DOMAIN}") | UserModel.email.like(f"%@{E2E_DOMAIN}")
            )
            .returning(UserModel.id)
        )
        return len(result.all())


async def seed_demo(
    sf: async_sessionmaker[AsyncSession],
    settings: Settings,
    *,
    reset: bool = False,
    now: datetime | None = None,
) -> DemoResult:
    now = now or datetime.now(UTC)
    removed = await remove_demo_accounts(sf) if reset else 0
    services = _Services(sf, settings)

    created = skipped = 0
    for learner in COHORT:
        if await services.users.get_by_email(learner.email) is not None:
            skipped += 1
            continue
        user = await services.register.execute(learner.email, DEMO_PASSWORD, learner.name)
        for step in learner.steps:
            await _run_step(services, user.id, step, now)
        created += 1
    return DemoResult(created, skipped, removed)
