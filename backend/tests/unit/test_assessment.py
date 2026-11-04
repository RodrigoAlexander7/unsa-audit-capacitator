from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from unsa_audit.assessment.application.errors import (
    AlreadySubmitted,
    AttemptNotFound,
    UnknownProfile,
)
from unsa_audit.assessment.application.use_cases import (
    GetAssessment,
    ListAssessments,
    StartAssessment,
    SubmitAssessment,
)
from unsa_audit.assessment.domain.assessment import (
    AssessmentDefinition,
    Attempt,
    AttemptStatus,
    InvalidAnswers,
    Option,
    Profile,
    Question,
    grade,
    ordered_question_ids,
    pct,
)
from unsa_audit.assessment.infrastructure.question_bank import (
    FileQuestionBank,
    QuestionBankError,
    load_definition,
)
from unsa_audit.documents.infrastructure.content_loader import FilePimsRequirementSource

CONTENT = Path(__file__).resolve().parents[3] / "content"
NOW = datetime(2026, 1, 1, tzinfo=UTC)


# ---------------------------------------------------------------------------- contenido


@pytest.fixture(scope="module")
def bank() -> FileQuestionBank:
    return FileQuestionBank(CONTENT)


@pytest.mark.ac("AC-006-9")
@pytest.mark.parametrize("profile", list(Profile))
def test_banco_valido_con_12_preguntas_y_competencias_suficientes(bank, profile) -> None:
    definition = bank.get(profile)
    assert definition is not None and definition.profile is profile
    assert len(definition.questions) == 12
    assert len({q.id for q in definition.questions}) == 12
    assert len({q.competency for q in definition.questions}) >= 5
    assert set(q.competency for q in definition.questions) <= set(definition.competencies)
    for q in definition.questions:
        ids = [o.id for o in q.options]
        assert len(ids) >= 3 and len(set(ids)) == len(ids) and q.correct in ids
        assert q.prompt and q.explanation


@pytest.mark.ac("AC-006-9")
def test_las_preguntas_referencian_requisitos_pims_existentes(bank) -> None:
    codes = {r.code for r in FilePimsRequirementSource(CONTENT).load()}
    for profile in Profile:
        used = {q.requirement_code for q in bank.get(profile).questions}  # type: ignore[union-attr]
        assert used <= codes, used - codes
        assert len(used) >= 5, "las preguntas cubren varios requisitos del PIMS"


@pytest.mark.ac("AC-006-9")
def test_los_perfiles_cubren_brechas_y_obligaciones_contractuales(bank) -> None:
    controller = {q.competency for q in bank.get(Profile.CONTROLLER).questions}  # type: ignore[union-attr]
    processor = {q.competency for q in bank.get(Profile.PROCESSOR).questions}  # type: ignore[union-attr]
    assert {"brechas", "encargados"} <= controller
    assert {"brechas", "instrucciones", "subencargados"} <= processor


@pytest.mark.ac("AC-006-9")
def test_la_respuesta_correcta_no_siempre_es_la_misma_letra(bank) -> None:
    for profile in Profile:
        letters = {q.correct for q in bank.get(profile).questions}  # type: ignore[union-attr]
        assert len(letters) >= 3


@pytest.mark.ac("AC-006-9")
def test_banco_roto_se_rechaza(tmp_path: Path) -> None:
    path = tmp_path / "x.json"
    base = {
        "profile": "controller", "title": "t", "pass_score": 70, "competencies": {"a": "A"},
        "questions": [{"id": "q1", "competency": "a", "requirement": "r", "prompt": "p",
                       "options": [{"id": "x", "label": "X"}, {"id": "y", "label": "Y"}],
                       "correct": "x", "explanation": "e"}],
    }  # fmt: skip
    import json

    path.write_text(json.dumps(base), encoding="utf-8")
    assert load_definition(path).questions[0].id == "q1"

    for mutate, message in [
        (lambda d: d["questions"][0].update(correct="z"), "opciones invalidas"),
        (lambda d: d["questions"][0].update(competency="zzz"), "competencia desconocida"),
        (lambda d: d.update(profile="otro"), "otro"),
        (lambda d: d["questions"].append(dict(d["questions"][0])), "repetidos"),
        (lambda d: d["questions"][0].pop("prompt"), "mal formada"),
    ]:
        data = json.loads(json.dumps(base))
        mutate(data)
        path.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(QuestionBankError, match=message):
            load_definition(path)


# ---------------------------------------------------------------------------- dominio

DEF = AssessmentDefinition(
    profile=Profile.CONTROLLER,
    title="t",
    pass_score=70,
    competencies={"a": "Comp A", "b": "Comp B"},
    questions=tuple(
        Question(
            id=f"q{i}",
            competency="a" if i < 3 else "b",
            requirement_code="req-1" if i % 2 == 0 else "req-2",
            prompt=f"P{i}",
            options=(Option("x", "X"), Option("y", "Y")),
            correct="x",
            explanation=f"E{i}",
        )
        for i in range(4)
    ),
)
LABELS = {"req-1": "1.1 Req uno", "req-2": "2.2 Req dos"}


@pytest.mark.ac("AC-006-11")
def test_correccion_con_puntajes_por_competencia_y_requisito() -> None:
    ids = ["q0", "q1", "q2", "q3"]
    result = grade(DEF, ids, {"q0": "x", "q1": "x", "q2": "y", "q3": "x"}, LABELS)
    assert (result.score, result.passed) == (75, True)
    comps = {g.key: (g.correct, g.total, g.percent) for g in result.competencies}
    assert comps == {"a": (2, 3, 67), "b": (1, 1, 100)}
    reqs = {g.key: (g.label, g.correct, g.total) for g in result.requirements}
    assert reqs == {"req-1": ("1.1 Req uno", 1, 2), "req-2": ("2.2 Req dos", 2, 2)}
    assert [i.correct for i in result.items] == [True, True, False, True]
    assert result.items[2].chosen_label == "Y" and result.items[2].correct_label == "X"
    assert result.items[2].explanation == "E2"


@pytest.mark.ac("AC-006-13")
def test_sin_responder_o_id_desconocido_es_incorrecto() -> None:
    result = grade(DEF, ["q0", "q1", "q2", "q3"], {"q0": "x", "zzz": "x", "q1": "no-existe"}, {})
    assert result.score == 25 and result.passed is False
    assert result.items[1].chosen_label is None and result.items[1].correct is False
    assert result.requirements[0].label == "req-1", "sin catalogo se usa el codigo"


@pytest.mark.ac("AC-006-13")
@pytest.mark.parametrize("bad", ["texto", ["x"], {"q0": 1}, {1: "x"}, None])
def test_forma_invalida_de_respuestas(bad) -> None:
    from unsa_audit.assessment.domain.assessment import validate_answers

    with pytest.raises(InvalidAnswers):
        validate_answers(bad)


@pytest.mark.ac("AC-006-10")
def test_orden_determinista_por_intento() -> None:
    first = ordered_question_ids(DEF, "intento-1")
    assert first == ordered_question_ids(DEF, "intento-1")
    assert sorted(first) == ["q0", "q1", "q2", "q3"]
    assert any(ordered_question_ids(DEF, f"i{n}") != first for n in range(10))
    assert pct(1, 3) == 33 and pct(0, 0) == 0


# ---------------------------------------------------------------------------- casos de uso


class FakeBank:
    def get(self, profile: Profile):
        return DEF if profile is Profile.CONTROLLER else None


class FakeCatalog:
    async def labels(self) -> dict[str, str]:
        return LABELS


class InMemoryAssessments:
    def __init__(self) -> None:
        self.items: dict[UUID, Attempt] = {}

    async def add(self, attempt: Attempt) -> None:
        self.items[attempt.id] = attempt

    async def get(self, attempt_id: UUID) -> Attempt | None:
        return self.items.get(attempt_id)

    async def save(self, attempt: Attempt) -> bool:
        if self.items[attempt.id].status is AttemptStatus.FINISHED:
            return False
        self.items[attempt.id] = attempt
        return True

    async def list_for_user(self, user_id: UUID) -> list[Attempt]:
        mine = [a for a in self.items.values() if a.user_id == user_id]
        return sorted(mine, key=lambda a: a.started_at, reverse=True)


@pytest.fixture
def repo() -> InMemoryAssessments:
    return InMemoryAssessments()


@pytest.mark.ac("AC-006-10")
async def test_iniciar_fija_las_preguntas_y_valida_el_perfil(repo) -> None:
    user = uuid4()
    view = await StartAssessment(FakeBank(), repo, clock=lambda: NOW).execute(
        user, Profile.CONTROLLER
    )
    assert view.attempt.status is AttemptStatus.IN_PROGRESS
    assert sorted(view.attempt.question_ids) == ["q0", "q1", "q2", "q3"]
    assert repo.items[view.attempt.id] == view.attempt
    with pytest.raises(UnknownProfile):
        await StartAssessment(FakeBank(), repo).execute(user, Profile.PROCESSOR)


@pytest.mark.ac("AC-006-11")
async def test_enviar_una_sola_vez_y_solo_el_dueno(repo) -> None:
    user, other = uuid4(), uuid4()
    start = StartAssessment(FakeBank(), repo, clock=lambda: NOW)
    view = await start.execute(user, Profile.CONTROLLER)
    submit = SubmitAssessment(FakeBank(), repo, FakeCatalog(), clock=lambda: NOW)

    with pytest.raises(AttemptNotFound):
        await submit.execute(other, view.attempt.id, {})
    with pytest.raises(AttemptNotFound):
        await GetAssessment(FakeBank(), repo).execute(other, view.attempt.id)
    with pytest.raises(AttemptNotFound):
        await submit.execute(user, uuid4(), {})
    with pytest.raises(InvalidAnswers):
        await submit.execute(user, view.attempt.id, "mal")
    assert repo.items[view.attempt.id].status is AttemptStatus.IN_PROGRESS, (
        "no se corrige si es invalido"
    )

    done = await submit.execute(user, view.attempt.id, {q: "x" for q in view.attempt.question_ids})
    assert done.attempt.status is AttemptStatus.FINISHED and done.attempt.finished_at == NOW
    assert done.attempt.result is not None and done.attempt.result.score == 100
    assert done.attempt.result.requirements[0].label.startswith(("1.1", "2.2"))
    with pytest.raises(AlreadySubmitted):
        await submit.execute(user, view.attempt.id, {})
    again = await GetAssessment(FakeBank(), repo).execute(user, view.attempt.id)
    assert again.attempt.result == done.attempt.result


@pytest.mark.ac("AC-006-12")
async def test_listar_mis_intentos_mas_recientes_primero(repo) -> None:
    user = uuid4()
    times = iter(datetime(2026, 1, d, tzinfo=UTC) for d in (1, 2, 3))
    start = StartAssessment(FakeBank(), repo, clock=lambda: next(times))
    ids = [(await start.execute(user, Profile.CONTROLLER)).attempt.id for _ in range(3)]
    await StartAssessment(FakeBank(), repo, clock=lambda: NOW).execute(uuid4(), Profile.CONTROLLER)
    listed = await ListAssessments(repo).execute(user)
    assert [a.id for a in listed] == list(reversed(ids))
