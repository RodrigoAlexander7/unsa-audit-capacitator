class AnalyticsError(Exception):
    """Error base del modulo analytics."""


class RouteStatsNotFound(AnalyticsError):
    pass


class InvalidQuestion(AnalyticsError):
    """Pregunta vacia o demasiado larga."""


class AdvisorUnavailable(AnalyticsError):
    """El asesor IA no pudo responder (comando ausente, error, respuesta invalida)."""


class AdvisorTimeout(AdvisorUnavailable):
    """El asesor IA excedio el tiempo maximo."""
