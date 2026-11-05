"""Casos de uso del asistente del estudiante."""

import time
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from unsa_audit.assistant.application.errors import (
    AssistantUnavailable,
    InvalidAssistantQuestion,
)
from unsa_audit.assistant.application.ports import (
    AssistantHistoryRepository,
    AssistantModelPort,
    StudentContextProvider,
)
from unsa_audit.assistant.domain.entities import (
    AssistantMessage,
    AssistantRole,
    AssistantStatus,
)
from unsa_audit.assistant.domain.guardrails import (
    QuestionValidationError,
    build_student_prompt,
    compute_context_hash,
    detect_guardrail_refusal,
    filter_model_output,
    sanitize_question,
    sanitize_route_path,
)

Clock = Callable[[], datetime]


def _utcnow() -> datetime:
    return datetime.now(UTC)


class AskStudentAssistant:
    def __init__(
        self,
        contexts: StudentContextProvider,
        model: AssistantModelPort,
        history: AssistantHistoryRepository,
        system_prompt: str,
        clock: Clock = _utcnow,
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._contexts = contexts
        self._model = model
        self._history = history
        self._system_prompt = system_prompt
        self._clock = clock
        self._id_factory = id_factory

    async def execute(
        self,
        user_id: UUID,
        raw_question: str,
        module_id: UUID | None = None,
        raw_route_path: str | None = None,
    ) -> AssistantMessage:
        try:
            question = sanitize_question(raw_question)
        except QuestionValidationError as exc:
            raise InvalidAssistantQuestion(str(exc)) from exc

        route_path = sanitize_route_path(raw_route_path)
        context = await self._contexts.build(module_id, route_path)

        refusal = detect_guardrail_refusal(question, has_exercise=context.has_exercise)
        if refusal is not None:
            message = AssistantMessage(
                id=self._id_factory(),
                user_id=user_id,
                role=AssistantRole.STUDENT.value,
                module_id=module_id,
                route_path=route_path,
                question=question,
                status=AssistantStatus.REFUSED.value,
                answer=refusal,
                error=None,
                context_hash=compute_context_hash(context),
                duration_ms=0,
                created_at=self._clock(),
            )
            await self._history.add(message)
            return message

        prompt, ctx_hash = build_student_prompt(self._system_prompt, context, question)
        started = time.monotonic()
        try:
            answer = await self._model.ask(prompt)
        except AssistantUnavailable as exc:
            elapsed = max(0, round((time.monotonic() - started) * 1000))
            await self._history.add(
                AssistantMessage(
                    id=self._id_factory(),
                    user_id=user_id,
                    role=AssistantRole.STUDENT.value,
                    module_id=module_id,
                    route_path=route_path,
                    question=question,
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
            user_id=user_id,
            role=AssistantRole.STUDENT.value,
            module_id=module_id,
            route_path=route_path,
            question=question,
            status=AssistantStatus.OK.value,
            answer=filter_model_output(answer.text),
            error=None,
            context_hash=ctx_hash,
            duration_ms=answer.duration_ms,
            created_at=self._clock(),
        )
        await self._history.add(message)
        return message


class ListStudentHistory:
    def __init__(self, history: AssistantHistoryRepository) -> None:
        self._history = history

    async def execute(self, user_id: UUID, limit: int = 30) -> list[AssistantMessage]:
        bounded = max(1, min(limit, 50))
        return await self._history.list_by_user(user_id, AssistantRole.STUDENT.value, bounded)


class ClearStudentHistory:
    def __init__(self, history: AssistantHistoryRepository) -> None:
        self._history = history

    async def execute(self, user_id: UUID) -> int:
        return await self._history.clear_by_user(user_id, AssistantRole.STUDENT.value)
