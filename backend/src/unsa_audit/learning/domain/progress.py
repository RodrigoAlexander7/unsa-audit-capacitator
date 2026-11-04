"""Reglas de progreso y bloqueo (puras)."""

from collections.abc import Collection

from unsa_audit.learning.domain.route import (
    Enrollment,
    EnrollmentStatus,
    Module,
    ModuleStatus,
    Route,
    RouteStatus,
)


def module_status(
    module: Module, route_modules: list[Module], completed_ids: Collection, enrolled: bool
) -> ModuleStatus:
    if module.id in completed_ids:
        return ModuleStatus.COMPLETED
    if module.planned or not enrolled:
        return ModuleStatus.LOCKED
    if module.is_final:
        pending = [
            m for m in route_modules if m.mandatory and not m.is_final and m.id not in completed_ids
        ]
        if pending:
            return ModuleStatus.LOCKED
    return ModuleStatus.AVAILABLE


def route_completed(route_modules: list[Module], completed_ids: Collection) -> bool:
    """Una ruta sin modulos publicados nunca se completa (los `planned` no cuentan)."""
    published = [m for m in route_modules if not m.planned]
    return bool(published) and all(m.id in completed_ids for m in published if m.mandatory)


def credited_minutes(route_modules: list[Module], completed_ids: Collection) -> int:
    return sum(m.minutes for m in route_modules if m.id in completed_ids)


def route_status(
    route: Route, enrollment: Enrollment | None, prerequisite: Enrollment | None
) -> RouteStatus:
    if enrollment is not None:
        if enrollment.status is EnrollmentStatus.COMPLETED:
            return RouteStatus.COMPLETED
        return RouteStatus.IN_PROGRESS
    if route.prerequisite_code is None:
        return RouteStatus.AVAILABLE
    if prerequisite is not None and prerequisite.status is EnrollmentStatus.COMPLETED:
        return RouteStatus.AVAILABLE
    return RouteStatus.LOCKED
