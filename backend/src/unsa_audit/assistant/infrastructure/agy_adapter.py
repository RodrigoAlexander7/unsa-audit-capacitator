"""Adaptador del modelo IA para el asistente usando AgyCliAdvisor."""

from unsa_audit.analytics.application.errors import AdvisorTimeout, AdvisorUnavailable
from unsa_audit.analytics.infrastructure.agy_advisor import AgyCliAdvisor
from unsa_audit.assistant.application.errors import AssistantTimeout, AssistantUnavailable
from unsa_audit.assistant.application.ports import ModelAnswer


class AgyStudentModelAdapter:
    def __init__(self, cli: AgyCliAdvisor) -> None:
        self._cli = cli

    async def ask(self, prompt: str) -> ModelAnswer:
        try:
            answer = await self._cli.ask(prompt)
        except AdvisorTimeout as exc:
            raise AssistantTimeout(str(exc)) from exc
        except AdvisorUnavailable as exc:
            raise AssistantUnavailable(str(exc)) from exc
        return ModelAnswer(text=answer.text, duration_ms=answer.duration_ms)
