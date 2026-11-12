"""Casos de uso del modo administrador y propuestas de reestructuracion."""

import time
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from unsa_audit.assistant.application.admin_ports import (
    AdminCohortProvider,
    CurriculumProposalRepository,
)
from unsa_audit.assistant.application.errors import (
    AssistantUnavailable,
    InvalidAssistantQuestion,
    InvalidProposalStatus,
    ProposalNotFound,
)
from unsa_audit.assistant.application.ports import (
    AssistantHistoryRepository,
    AssistantModelPort,
)
from unsa_audit.assistant.domain.admin_cohort import (
    AdminCohortSnapshot,
    CurriculumProposal,
    ProposalParseError,
    ProposalStatus,
    build_admin_cohort_prompt,
    build_restructuring_prompt,
    compute_admin_context_hash,
    parse_restructuring_proposals,
    pseudonymize_admin_question,
)
from unsa_audit.assistant.domain.entities import (
    AssistantMessage,
    AssistantRole,
    AssistantStatus,
)
from unsa_audit.assistant.domain.guardrails import (
    QuestionValidationError,
    detect_guardrail_refusal,
    filter_model_output,
    sanitize_question,
)

Clock = Callable[[], datetime]


def _utcnow() -> datetime:
    return datetime.now(UTC)


class GetAdminCohortSummary:
    def __init__(self, cohort: AdminCohortProvider) -> None:
        self._cohort = cohort

    async def execute(self) -> AdminCohortSnapshot:
        return await self._cohort.snapshot()


class AskAdminAssistant:
    def __init__(
        self,
        cohort: AdminCohortProvider,
        model: AssistantModelPort,
        history: AssistantHistoryRepository,
        system_prompt: str,
        clock: Clock = _utcnow,
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._cohort = cohort
        self._model = model
        self._history = history
        self._system_prompt = system_prompt
        self._clock = clock
        self._id_factory = id_factory

    async def execute(
        self, admin_id: UUID, raw_question: str
    ) -> tuple[AssistantMessage, AdminCohortSnapshot]:
        try:
            question = sanitize_question(raw_question)
        except QuestionValidationError as exc:
            raise InvalidAssistantQuestion(str(exc)) from exc

        snapshot = await self._cohort.snapshot()
        safe_question = pseudonymize_admin_question(question, snapshot.learners)
        ctx_hash = compute_admin_context_hash(snapshot)

        refusal = detect_guardrail_refusal(safe_question, has_exercise=False)
        if refusal is not None:
            message = AssistantMessage(
                id=self._id_factory(),
                user_id=admin_id,
                role=AssistantRole.ADMIN.value,
                module_id=None,
                route_path="/admin",
                question=safe_question,
                status=AssistantStatus.REFUSED.value,
                answer=refusal,
                error=None,
                context_hash=ctx_hash,
                duration_ms=0,
                created_at=self._clock(),
            )
            await self._history.add(message)
            return message, snapshot

        prompt, ctx_hash = build_admin_cohort_prompt(self._system_prompt, snapshot, safe_question)
        started = time.monotonic()
        try:
            answer = await self._model.ask(prompt)
        except AssistantUnavailable as exc:
            elapsed = max(0, round((time.monotonic() - started) * 1000))
            await self._history.add(
                AssistantMessage(
                    id=self._id_factory(),
                    user_id=admin_id,
                    role=AssistantRole.ADMIN.value,
                    module_id=None,
                    route_path="/admin",
                    question=safe_question,
                    status=AssistantStatus.ERROR.value,
                    answer=None,
                    error=str(exc),
                    context_hash=ctx_hash,
                    duration_ms=elapsed,
                    created_at=self._clock(),
                )
            )
            raise

        message = AssistantMessage(
            id=self._id_factory(),
            user_id=admin_id,
            role=AssistantRole.ADMIN.value,
            module_id=None,
            route_path="/admin",
            question=safe_question,
            status=AssistantStatus.OK.value,
            answer=filter_model_output(answer.text),
            error=None,
            context_hash=ctx_hash,
            duration_ms=answer.duration_ms,
            created_at=self._clock(),
        )
        await self._history.add(message)
        return message, snapshot


class ListAdminHistory:
    def __init__(self, history: AssistantHistoryRepository) -> None:
        self._history = history

    async def execute(self, admin_id: UUID, limit: int = 30) -> list[AssistantMessage]:
        bounded = max(1, min(limit, 50))
        return await self._history.list_by_user(admin_id, AssistantRole.ADMIN.value, bounded)


class ClearAdminHistory:
    def __init__(self, history: AssistantHistoryRepository) -> None:
        self._history = history

    async def execute(self, admin_id: UUID) -> int:
        return await self._history.clear_by_user(admin_id, AssistantRole.ADMIN.value)


class GenerateRestructuringProposals:
    def __init__(
        self,
        cohort: AdminCohortProvider,
        model: AssistantModelPort,
        proposals: CurriculumProposalRepository,
        system_prompt: str,
        clock: Clock = _utcnow,
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._cohort = cohort
        self._model = model
        self._proposals = proposals
        self._system_prompt = system_prompt
        self._clock = clock
        self._id_factory = id_factory

    async def execute(
        self, admin_id: UUID, focus: str | None = None, route_code: str | None = None
    ) -> tuple[str, list[CurriculumProposal]]:
        snapshot = await self._cohort.snapshot()
        clean_focus = focus.strip()[:400] if focus and focus.strip() else None
        if clean_focus:
            clean_focus = pseudonymize_admin_question(clean_focus, snapshot.learners)
        target_route = route_code.strip() if route_code and route_code.strip() else None
        if target_route and target_route not in snapshot.valid_route_codes:
            target_route = None

        prompt, ctx_hash = build_restructuring_prompt(
            self._system_prompt, snapshot, clean_focus, target_route
        )
        answer = await self._model.ask(prompt)
        try:
            summary, items = parse_restructuring_proposals(
                answer.text,
                snapshot.valid_route_codes,
                created_by=admin_id,
                context_hash=ctx_hash,
                now=self._clock(),
                id_factory=self._id_factory,
            )
        except ProposalParseError as exc:
            raise AssistantUnavailable(str(exc)) from exc

        await self._proposals.add_many(items)
        return summary, items


class ListCurriculumProposals:
    def __init__(self, proposals: CurriculumProposalRepository) -> None:
        self._proposals = proposals

    async def execute(self, limit: int = 30) -> list[CurriculumProposal]:
        return await self._proposals.list_recent(max(1, min(limit, 50)))


class ReviewCurriculumProposal:
    def __init__(self, proposals: CurriculumProposalRepository, clock: Clock = _utcnow) -> None:
        self._proposals = proposals
        self._clock = clock

    async def execute(
        self, proposal_id: UUID, raw_status: str, review_note: str | None = None
    ) -> CurriculumProposal:
        try:
            new_status = ProposalStatus(raw_status)
        except ValueError as exc:
            raise InvalidProposalStatus("Estado de propuesta inválido.") from exc

        existing = await self._proposals.get(proposal_id)
        if existing is None:
            raise ProposalNotFound("Propuesta no encontrada.")

        clean_note = review_note.strip()[:600] if review_note and review_note.strip() else None
        reviewed_at = None if new_status == ProposalStatus.DRAFT else self._clock()
        updated = replace(
            existing,
            status=new_status.value,
            review_note=clean_note if review_note is not None else existing.review_note,
            reviewed_at=reviewed_at,
        )
        return await self._proposals.update_status(updated)
