from dataclasses import dataclass
from typing import Protocol


class DatabaseProbe(Protocol):
    """Puerto: comprueba si la base de datos responde."""

    async def is_up(self) -> bool: ...


@dataclass(frozen=True)
class HealthReport:
    database_up: bool

    @property
    def status(self) -> str:
        return "ok" if self.database_up else "degraded"


class CheckHealth:
    def __init__(self, probe: DatabaseProbe) -> None:
        self._probe = probe

    async def execute(self) -> HealthReport:
        return HealthReport(database_up=await self._probe.is_up())
