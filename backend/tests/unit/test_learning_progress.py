from datetime import UTC, datetime
from uuid import uuid4

import pytest

from unsa_audit.learning.domain.progress import (
    credited_minutes,
    module_status,
    route_completed,
    route_status,
)
from unsa_audit.learning.domain.route import (
    Enrollment,
    EnrollmentStatus,
    Module,
    ModuleStatus,
    Route,
    RouteStatus,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _module(
    order: int, *, final: bool = False, mandatory: bool = True, minutes: int = 60
) -> Module:
    return Module(
        uuid4(), "r1", f"m{order}", order, f"M{order}", minutes, mandatory, final, "", None
    )


def _enrollment(route: str, status: EnrollmentStatus) -> Enrollment:
    return Enrollment(uuid4(), route, status, NOW)


@pytest.mark.ac("AC-003-5")
def test_sin_matricula_todo_bloqueado() -> None:
    mods = [_module(1), _module(2)]
    assert all(module_status(m, mods, set(), enrolled=False) is ModuleStatus.LOCKED for m in mods)


@pytest.mark.ac("AC-003-10")
def test_el_modulo_final_se_desbloquea_al_completar_los_demas_obligatorios() -> None:
    m1, m2, optional, final = (
        _module(1),
        _module(2),
        _module(3, mandatory=False),
        _module(4, final=True),
    )
    mods = [m1, m2, optional, final]
    assert module_status(final, mods, {m1.id}, True) is ModuleStatus.LOCKED
    assert (
        module_status(final, mods, {m1.id, m2.id}, True) is ModuleStatus.AVAILABLE
    )  # opcional no cuenta
    assert module_status(m1, mods, set(), True) is ModuleStatus.AVAILABLE
    assert module_status(m1, mods, {m1.id}, True) is ModuleStatus.COMPLETED


@pytest.mark.ac("AC-003-11")
def test_ruta_completa_solo_con_modulos_y_todos_los_obligatorios() -> None:
    m1, m2, optional = _module(1), _module(2), _module(3, mandatory=False)
    assert not route_completed([], set()), "una ruta sin modulos nunca se completa"
    assert not route_completed([m1, m2, optional], {m1.id})
    assert route_completed([m1, m2, optional], {m1.id, m2.id})


@pytest.mark.ac("AC-003-12")
def test_minutos_acreditados_suman_solo_modulos_completados() -> None:
    m1, m2 = _module(1, minutes=100), _module(2, minutes=50)
    assert credited_minutes([m1, m2], {m1.id}) == 100
    assert credited_minutes([m1, m2], set()) == 0


@pytest.mark.ac("AC-003-1")
def test_estado_de_ruta_segun_matricula_y_prerrequisito() -> None:
    r1 = Route("r1", 1, "R1", "", 12, None)
    r2 = Route("r2", 2, "R2", "", 16, "r1")
    done, going = (
        _enrollment("r1", EnrollmentStatus.COMPLETED),
        _enrollment("r1", EnrollmentStatus.IN_PROGRESS),
    )
    assert route_status(r1, None, None) is RouteStatus.AVAILABLE
    assert route_status(r2, None, None) is RouteStatus.LOCKED
    assert route_status(r2, None, going) is RouteStatus.LOCKED
    assert route_status(r2, None, done) is RouteStatus.AVAILABLE
    assert route_status(r1, going, None) is RouteStatus.IN_PROGRESS
    assert route_status(r1, done, None) is RouteStatus.COMPLETED
