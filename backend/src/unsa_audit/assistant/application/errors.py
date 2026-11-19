"""Excepciones de aplicacion del modulo assistant."""


class AssistantError(Exception):
    """Error base del asistente."""


class InvalidAssistantQuestion(AssistantError):
    """Pregunta vacia, invalida o excede el limite permitido."""


class AssistantUnavailable(AssistantError):
    """El modelo IA no pudo responder o devolvio salida invalida."""


class AssistantTimeout(AssistantUnavailable):
    """El modelo IA excedio el tiempo limite."""


class ProposalNotFound(AssistantError):
    """No existe la propuesta de reestructuracion solicitada."""


class InvalidProposalStatus(AssistantError):
    """Estado de revision de propuesta no permitido."""
