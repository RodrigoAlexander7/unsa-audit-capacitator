import json
from datetime import UTC, date, datetime
from uuid import UUID, uuid4

import pytest

from unsa_audit.analytics.application.errors import (
    AdvisorTimeout,
    AdvisorUnavailable,
    InvalidQuestion,
    RouteStatsNotFound,
)
from unsa_audit.analytics.application.ports import (
    AdvisorAnswer,
    PimsRequirementState,
    PimsSummary,
)
from unsa_audit.analytics.application.use_cases import (
    AskAdvisor,
    BuildSnapshot,
    GetRouteDetailStats,
    ListAdvisorHistory,
    build_prompt,
)
from unsa_audit.analytics.domain.stats import (
    AdvisorQuery,
    AssessmentProfileStats,
    GroupAverage,
    ModuleStats,
    ParticipantCounts,
    RouteStats,
    hardest_modules,
    percent,
)

NOW = datetime(2026, 11, 11, 12, 0, tzinfo=UTC)


def _module(order: int, attempts: int, passed_pct: int | None, avg: int | None, route="r1"):
    return ModuleStats(uuid4(), route, order, f"Modulo {order}", 60, False, attempts, attempts,
                       0, avg, passed_pct)  # fmt: skip


# ---------------------------------------------------------------------------- dominio


@pytest.mark.ac("AC-007-2")
def test_modulos_dificiles_menor_aprobacion_con_intentos_suficientes() -> None:
    easy = _module(1, 10, 100, 95)
    hard = _module(2, 6, 33, 40)
    harder = _module(3, 4, 25, 30)
    few = _module(4, 2, 0, 0)  # pocos intentos: no cuenta
    none = _module(5, 0, None, None)
    ids = hardest_modules([easy, hard, harder, few, none], limit=2)
    assert ids == {hard.id, harder.id}
    assert hardest_modules([easy]) == set(), "uno perfecto nunca es dificil"
    assert percent(1, 3) == 33 and percent(0, 0) == 0 and percent(2, 3) == 67


# ---------------------------------------------------------------------------- snapshot

ROUTE = RouteStats("r1", 1, "Ruta Uno", 12, 7, 4, 3, 1, 25, 36, 3.5, 13, 77, 1)
MOD = _module(3, 4, 50, 55)
ASSESSMENT = AssessmentProfileStats(
    "controller", 2, 80, 50,
    [GroupAverage("brechas", "Gestión de brechas", 40, 2)],
    [GroupAverage("pims-soa", "6.1.3 e Declaración de aplicabilidad (SoA)", 75, 2)],
)  # fmt: skip


class FakeAnalytics:
    def __init__(self, routes=None, modules=None) -> None:
        self.routes = [ROUTE] if routes is None else routes
        self.modules = [MOD] if modules is None else modules

    async def route_stats(self, now):
        return self.routes

    async def module_stats(self, route_code=None):
        return [m for m in self.modules if route_code in (None, m.route_code)]

    async def assessment_stats(self):
        return [ASSESSMENT]

    async def participants(self, now):
        return ParticipantCounts(4, 2)


class FakePims:
    async def summary(self) -> PimsSummary:
        return PimsSummary(
            date(2026, 11, 11), 11, 5,
            {"in_force": 5, "draft": 2, "expired": 2, "unowned": 1, "missing": 1},
            [PimsRequirementState("4.3", "Alcance del PIMS", "in_force")],
            open_change_requests=3,
        )  # fmt: skip


def _snapshots(analytics=None, clock_time=NOW):
    return BuildSnapshot(analytics or FakeAnalytics(), FakePims(), clock=lambda: clock_time)


@pytest.mark.ac("AC-007-4")
async def test_snapshot_agregado_con_rutas_modulos_evaluaciones_y_pims() -> None:
    snap = await _snapshots().execute()
    data = snap.data
    assert data["participants"] == {"total": 4, "new_last_7_days": 2}
    route = data["routes"][0]
    assert (route["title"], route["enrolled"], route["completion_rate_pct"]) == ("Ruta Uno", 4, 25)
    assert route["stalled_last_7_days"] == 1 and route["planned_hours"] == 12
    module = data["modules"][0]
    assert (module["route"], module["pass_rate_pct"], module["among_hardest"]) == (
        "Ruta Uno",
        50,
        True,
    )
    assessment = data["assessments"][0]
    assert assessment["competencies"][0] == {
        "name": "Gestión de brechas", "avg_correct_pct": 40, "evaluations": 2,
    }  # fmt: skip
    assert data["pims_documents"]["by_state"]["missing"] == 1
    assert data["pims_documents"]["open_change_requests"] == 3


@pytest.mark.ac("AC-007-4")
async def test_snapshot_es_determinista_y_su_hash_ignora_la_fecha() -> None:
    a = await _snapshots().execute()
    b = await _snapshots(clock_time=datetime(2027, 1, 1, tzinfo=UTC)).execute()
    assert a.hash == b.hash and a.data["generated_at"] != b.data["generated_at"]
    changed = await _snapshots(FakeAnalytics(modules=[])).execute()
    assert changed.hash != a.hash


@pytest.mark.ac("AC-007-4")
async def test_snapshot_no_contiene_identificadores_de_personas() -> None:
    snap = await _snapshots().execute()
    text = json.dumps(snap.data, ensure_ascii=False)
    keys: set[str] = set()

    def walk(value):
        if isinstance(value, dict):
            keys.update(value)
            for v in value.values():
                walk(v)
        elif isinstance(value, list):
            for v in value:
                walk(v)

    walk(snap.data)
    assert not keys & {"email", "user_id", "full_name", "name_of_user", "asked_by", "id"}
    assert "@" not in text


# ---------------------------------------------------------------------------- estadisticas de ruta


@pytest.mark.ac("AC-007-2")
async def test_detalle_de_ruta_marca_dificiles_y_404() -> None:
    hard, easy = _module(2, 6, 33, 40), _module(1, 5, 100, 95)
    other = _module(1, 9, 10, 10, route="r2")
    use_case = GetRouteDetailStats(FakeAnalytics(modules=[hard, easy, other]), clock=lambda: NOW)
    detail = await use_case.execute("r1")
    assert [m.order for m in detail.modules] == [1, 2]
    assert [m.hardest for m in detail.modules] == [False, True]
    assert detail.route.code == "r1"
    with pytest.raises(RouteStatsNotFound):
        await use_case.execute("nada")


# ---------------------------------------------------------------------------- asesor


class FakeAdvisor:
    def __init__(self, text: str = "## Diagnóstico\nTodo bien.", error: Exception | None = None):
        self.text, self.error, self.prompts = text, error, []

    async def ask(self, prompt: str) -> AdvisorAnswer:
        self.prompts.append(prompt)
        if self.error:
            raise self.error
        return AdvisorAnswer(self.text, 42)


class InMemoryQueries:
    def __init__(self) -> None:
        self.items: list[AdvisorQuery] = []

    async def add(self, query: AdvisorQuery) -> None:
        self.items.append(query)

    async def list_recent(self, limit: int) -> list[AdvisorQuery]:
        return sorted(self.items, key=lambda q: q.created_at, reverse=True)[:limit]


SYSTEM = "REGLAS-DEL-SISTEMA: responde en español."


def _ask(advisor, queries):
    return AskAdvisor(_snapshots(), advisor, queries, SYSTEM, clock=lambda: NOW)


@pytest.mark.ac("AC-007-8")
def test_el_prompt_tiene_sistema_datos_y_pregunta_una_sola_vez() -> None:
    prompt = build_prompt(SYSTEM, {"routes": [{"title": "Ruta Uno"}]}, "  ¿Cómo están?  ")
    assert prompt.count("REGLAS-DEL-SISTEMA") == 1
    assert prompt.count("PREGUNTA: ¿Cómo están?") == 1
    assert prompt.count("Ruta Uno") == 1 and "DATOS" in prompt
    assert not prompt.lstrip().startswith("-"), "no empieza con un guion (no parece un flag)"


@pytest.mark.ac("AC-007-6")
async def test_preguntar_registra_la_consulta_con_la_respuesta() -> None:
    advisor, queries, user = FakeAdvisor(), InMemoryQueries(), uuid4()
    query = await _ask(advisor, queries).execute(
        user, "  ¿Cómo están los alumnos de sensibilización? "
    )
    assert query.status == "ok" and (query.answer or "").startswith("## Diagnóstico")
    assert (query.asked_by, query.duration_ms, query.created_at) == (user, 42, NOW)
    assert query.question == "¿Cómo están los alumnos de sensibilización?"
    assert queries.items == [query] and len(query.snapshot_hash) == 64

    prompt = advisor.prompts[0]
    assert prompt.count("alumnos de sensibilización") == 1 and prompt.count(SYSTEM) == 1
    assert '"Ruta Uno"' in prompt, "incluye el snapshot"


@pytest.mark.ac("AC-007-6")
@pytest.mark.parametrize("error", [AdvisorUnavailable("sin comando"), AdvisorTimeout("lento")])
async def test_si_el_asesor_falla_se_registra_el_error_y_se_propaga(error) -> None:
    queries = InMemoryQueries()
    with pytest.raises(AdvisorUnavailable):
        await _ask(FakeAdvisor(error=error), queries).execute(uuid4(), "¿Hola?")
    assert len(queries.items) == 1
    stored = queries.items[0]
    assert (stored.status, stored.answer, stored.error) == ("error", None, str(error))


@pytest.mark.ac("AC-007-6")
@pytest.mark.parametrize("question", ["", "   ", "x" * 1001])
async def test_pregunta_invalida_no_llama_al_asesor_ni_registra(question) -> None:
    advisor, queries = FakeAdvisor(), InMemoryQueries()
    with pytest.raises(InvalidQuestion):
        await _ask(advisor, queries).execute(uuid4(), question)
    assert advisor.prompts == [] and queries.items == []


@pytest.mark.ac("AC-007-7")
async def test_historial_mas_reciente_primero_y_limitado() -> None:
    queries = InMemoryQueries()
    for day in range(1, 4):
        queries.items.append(
            AdvisorQuery(
                uuid4(),
                None,
                f"q{day}",
                "h",
                "ok",
                "a",
                None,
                1,
                datetime(2026, 1, day, tzinfo=UTC),
            )  # fmt: skip
        )
    history = await ListAdvisorHistory(queries).execute(2)
    assert [q.question for q in history] == ["q3", "q2"]
    assert isinstance(history[0].id, UUID)
