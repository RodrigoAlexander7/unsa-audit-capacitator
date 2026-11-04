class AssessmentError(Exception):
    """Error base del modulo assessment."""


class AttemptNotFound(AssessmentError):
    """No existe el intento o no pertenece al usuario."""


class AlreadySubmitted(AssessmentError):
    pass


class UnknownProfile(AssessmentError):
    """No hay banco de preguntas para el perfil."""
