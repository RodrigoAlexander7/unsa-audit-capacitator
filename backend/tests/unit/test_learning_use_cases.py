from datetime import UTC, datetime
from uuid import uuid4

import pytest

from tests.solutions import solve, wrong
from tests.unit.fakes_learning import FakeFacts, InMemoryLearningRepository
from unsa_audit.learning.application.errors import (
    HasExercise,
    ModuleLocked,
    ModuleNotFound,
    NotEnrolled,
    PrerequisiteNotMet,
    RouteNotFound,
)
from unsa_audit.learning.application.use_cases import (
    CompleteReadingModule,
    EnrollInRoute,
    GetModule,
    GetRoute,
    ListRoutes,
    SubmitAttempt,
    SyncContent,
)
from unsa_audit.learning.domain.exercises import InvalidAnswer
from unsa_audit.learning.domain.route import (
    EnrollmentStatus,
    ExerciseDef,
    ExerciseKind,
    Module,
    ModuleStatus,
    Route,
    RouteStatus,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)
CHOICE = {
    "prompt": "Elige",
    "options": [{"id": "a", "label": "A"}, {"id": "b", "label": "B"}],
    "correct": "a",
}


def _module(route: str, order: int, minutes: int, *, final=False, exercise=True, mandatory=True):
    ex = ExerciseDef(ExerciseKind.SINGLE_CHOICE, CHOICE) if exercise else None
    return Module(
        uuid4(), route, f"m{order}", order, f"M{order}", minutes, mandatory, final, "# L", ex
    )


ROUTES = [
    Route("r1", 1, "R1", "", 1, None),
    Route("r2", 2, "R2", "", 1, "r1"),
    Route("r3", 3, "R3", "", 1, "r2"),
]


@pytest.fixture
def modules() -> list[Module]:
    return [
        _module("r1", 1, 30),
        _module("r1", 2, 30, exercise=False),  # solo lectura
        _module("r1", 3, 60, final=True),
    ]


@pytest.fixture
def repo(modules: list[Module]) -> InMemoryLearningRepository:
    return InMemoryLearningRepository(ROUTES, modules)


@pytest.fixture
def user():
    return uuid4()


def _enroll(repo):
    return EnrollInRoute(repo, clock=lambda: NOW)


def _submit(repo):
    return SubmitAttempt(repo, FakeFacts(), clock=lambda: NOW)


GOOD = solve(ExerciseKind.SINGLE_CHOICE, CHOICE)
BAD = wrong(ExerciseKind.SINGLE_CHOICE)


@pytest.mark.ac("AC-003-2")
async def test_matricula_es_idempotente(repo, user) -> None:
    first, created = await _enroll(repo).execute(user, "r1")
    again, created_again = await _enroll(repo).execute(user, "r1")
    assert created and not created_again
    assert first == again and first.status is EnrollmentStatus.IN_PROGRESS


@pytest.mark.ac("AC-003-3")
async def test_no_se_puede_matricular_sin_aprobar_el_prerrequisito(repo, user) -> None:
    with pytest.raises(PrerequisiteNotMet) as exc:
        await _enroll(repo).execute(user, "r2")
    assert exc.value.prerequisite_code == "r1"
    await _enroll(repo).execute(user, "r1")  # matriculado pero no aprobado
    with pytest.raises(PrerequisiteNotMet):
        await _enroll(repo).execute(user, "r2")
    with pytest.raises(PrerequisiteNotMet):
        await _enroll(repo).execute(user, "r3")


@pytest.mark.ac("AC-003-4")
async def test_ruta_inexistente(repo, user) -> None:
    with pytest.raises(RouteNotFound):
        await _enroll(repo).execute(user, "nada")
    with pytest.raises(RouteNotFound):
        await GetRoute(repo).execute(user, "nada")


@pytest.mark.ac("AC-003-6")
async def test_modulo_exige_matricula_y_existir(repo, modules, user) -> None:
    with pytest.raises(NotEnrolled):
        await GetModule(repo, FakeFacts()).execute(user, modules[0].id)
    with pytest.raises(ModuleNotFound):
        await GetModule(repo, FakeFacts()).execute(user, uuid4())
    await _enroll(repo).execute(user, "r1")
    view = await GetModule(repo, FakeFacts()).execute(user, modules[0].id)
    assert view.public_exercise is not None and "correct" not in view.public_exercise["options"][0]


@pytest.mark.ac("AC-003-8")
async def test_intento_incorrecto_no_completa_y_correcto_si(repo, modules, user) -> None:
    await _enroll(repo).execute(user, "r1")
    bad = await _submit(repo).execute(user, modules[0].id, BAD)
    assert (bad.score, bad.passed, bad.module_completed) == (0, False, False)
    assert (user, modules[0].id) in repo.progress and not repo.progress[
        (user, modules[0].id)
    ].completed
    good = await _submit(repo).execute(user, modules[0].id, GOOD)
    assert (good.score, good.passed, good.module_completed) == (100, True, True)
    progress = repo.progress[(user, modules[0].id)]
    assert progress.minutes_credited == 30 and progress.best_score == 100


@pytest.mark.ac("AC-003-8")
async def test_respuesta_con_forma_invalida_no_guarda_nada(repo, modules, user) -> None:
    await _enroll(repo).execute(user, "r1")
    with pytest.raises(InvalidAnswer):
        await _submit(repo).execute(user, modules[0].id, {"choice": 5})
    assert not repo.attempts and not repo.progress


@pytest.mark.ac("AC-003-14")
async def test_cada_intento_queda_registrado(repo, modules, user) -> None:
    await _enroll(repo).execute(user, "r1")
    await _submit(repo).execute(user, modules[0].id, BAD)
    await _submit(repo).execute(user, modules[0].id, GOOD)
    assert [(a.score, a.passed) for a in repo.attempts] == [(0, False), (100, True)]
    assert repo.attempts[0].answer == BAD and repo.attempts[0].created_at == NOW


@pytest.mark.ac("AC-003-10")
@pytest.mark.ac("AC-003-11")
async def test_final_bloqueado_hasta_completar_y_la_ruta_se_aprueba(repo, modules, user) -> None:
    await _enroll(repo).execute(user, "r1")
    with pytest.raises(ModuleLocked):
        await _submit(repo).execute(user, modules[2].id, GOOD)

    await _submit(repo).execute(user, modules[0].id, GOOD)
    with pytest.raises(ModuleLocked):  # falta el modulo de lectura
        await _submit(repo).execute(user, modules[2].id, GOOD)

    done = await CompleteReadingModule(repo, clock=lambda: NOW).execute(user, modules[1].id)
    assert done.module_completed and not done.route_completed

    final = await _submit(repo).execute(user, modules[2].id, GOOD)
    assert final.route_completed
    enrollment = await repo.get_enrollment(user, "r1")
    assert enrollment and enrollment.status is EnrollmentStatus.COMPLETED
    assert enrollment.completed_at == NOW

    listing = await ListRoutes(repo).execute(user)
    r1, r2, _ = listing.routes
    assert (r1.status, r1.minutes_credited, r1.hours_credited) is not None
    assert r1.status is RouteStatus.COMPLETED and r1.hours_credited == 2.0
    assert r2.status is RouteStatus.AVAILABLE
    assert listing.total_hours_credited == 2.0
    # ahora si puede matricularse en R2
    _, created = await _enroll(repo).execute(user, "r2")
    assert created


@pytest.mark.ac("AC-003-12")
async def test_reintentar_no_acredita_horas_otra_vez_y_conserva_el_mejor_puntaje(
    repo, modules, user
) -> None:
    await _enroll(repo).execute(user, "r1")
    await _submit(repo).execute(user, modules[0].id, GOOD)
    again = await _submit(repo).execute(user, modules[0].id, BAD)
    assert again.score == 0 and again.module_completed, "sigue completado"
    progress = repo.progress[(user, modules[0].id)]
    assert progress.minutes_credited == 30 and progress.best_score == 100 and progress.completed
    listing = await ListRoutes(repo).execute(user)
    assert listing.routes[0].minutes_credited == 30


@pytest.mark.ac("AC-003-13")
async def test_modulo_de_lectura_se_completa_y_uno_con_ejercicio_no(repo, modules, user) -> None:
    await _enroll(repo).execute(user, "r1")
    with pytest.raises(HasExercise):
        await CompleteReadingModule(repo).execute(user, modules[0].id)
    result = await CompleteReadingModule(repo, clock=lambda: NOW).execute(user, modules[1].id)
    assert result.module_completed
    # idempotente
    await CompleteReadingModule(repo, clock=lambda: NOW).execute(user, modules[1].id)
    assert repo.progress[(user, modules[1].id)].minutes_credited == 30


@pytest.mark.ac("AC-003-11")
async def test_ruta_sin_modulos_se_puede_cursar_pero_nunca_se_completa(user) -> None:
    repo = InMemoryLearningRepository(ROUTES, [])
    await _enroll(repo).execute(user, "r1")
    detail = await GetRoute(repo).execute(user, "r1")
    assert detail.summary.status is RouteStatus.IN_PROGRESS
    assert detail.modules == [] and detail.summary.modules_total == 0


@pytest.mark.ac("AC-003-5")
async def test_detalle_de_ruta_con_estado_por_modulo(repo, modules, user) -> None:
    before = await GetRoute(repo).execute(user, "r1")
    assert {m.status for m in before.modules} == {ModuleStatus.LOCKED}
    await _enroll(repo).execute(user, "r1")
    after = await GetRoute(repo).execute(user, "r1")
    assert [m.status for m in after.modules] == [
        ModuleStatus.AVAILABLE, ModuleStatus.AVAILABLE, ModuleStatus.LOCKED,
    ]  # fmt: skip


@pytest.mark.ac("AC-003-16")
async def test_sync_reemplaza_el_contenido(modules) -> None:
    repo = InMemoryLearningRepository()

    class Source:
        def load(self):
            return ROUTES, modules

    assert await SyncContent(repo, Source()).execute() == (3, 3)
    assert len(await repo.list_modules()) == 3
